"""Loads specific custom properties from Chef to SolarWinds through API"""
from custom_property_loader.chef_interface import ChefAPI
from custom_property_loader.sw_interface import SolarWindsInterface
import os
from tools.tools import Tools
from tools.tools import timer


def loader_menu(chef, sw, tool_bag, nodes):
    """Creates menu for selecting which custom property to load"""
    menu_items = ["Chef_Environment",
                  "Chef_Management_Group",
                  "Chef_Patching_Role",
                  "Chef_Other_Roles",
                  "Exit"]

    if os.name == "posix":
        os.system('clear')
    else:
        os.system('CLS')

    while True:
        print("Select field to load from Chef to SolarWinds")
        print(f"Enter menu number between 1 and {len(menu_items)}")
        for item in menu_items:
            print(f"[{menu_items.index(item) + 1}] {item}")
        choice = int(input(">> ")) - 1
        try:
            if choice < 0:
                raise ValueError
            menu_items[choice]
        except (ValueError, IndexError):
            print("Invalid menu selection. Please try again.")
            pass
        if choice == 0:
            load_properties(chef, sw, nodes,
                            "Chef_Environment")
        elif choice == 1:
            managed_role_path = "data/managed_roles.csv"
            managed_role = tool_bag.csv_pull_key(managed_role_path, 0)
            load_properties(chef, sw, nodes,
                            "Chef_Management_Group",
                            data=managed_role)
        elif choice == 2:
            patching_role_path = "data/patching_roles.csv"
            patching_role = tool_bag.csv_pull_key(patching_role_path, 0)
            load_properties(chef, sw, nodes,
                            "Chef_Patching_Role",
                            data=patching_role)
        elif choice == 3:
            other_role_path = 'data/other_roles.csv'
            other_role = tool_bag.csv_pull_key(other_role_path, 0)
            load_properties(chef, sw, nodes,
                            "Chef_Other_Roles",
                            data=other_role)
        else:
            break


@timer
def load_properties(chef, sw, nodes, prop, data=[]):
    """Loads specific custom property as selected by the menu"""
    node_names = {node['NodeName']: node['Uri'] for node in nodes}
    node_props = {}
    node_props['Property'] = prop
    total = len(node_names)
    count = 0

    for node, uri in node_names.items():
        node = node.lower()
        check = False
        upper = False
        node_props['Name'] = node
        node_props['Uri'] = uri
        while check is False:
            response = chef.chef_search(
                    index='node',
                    query=f'name:{node} OR name:{node}.state.de.us OR name:{node}.dti.state.de.us')
            if response['total'] == 0:
                if upper is False:
                    node = node.upper()
                    upper = True
                else:
                    node_props['Value'] = 'not-found'
                    check = True
            else:
                response = response['rows'][0]
                try:
                    if(prop == "Chef_Environment"):
                        node_props['Value'] = response[prop.lower()]
                    else:
                        run_list = [cleaner(word) for word in response['run_list']]
                        node_patching_role = list(
                            set(run_list) & set(data))
                        node_props['Value'] = ", ".join(node_patching_role)
                        if len(node_props['Value']) == 0:
                            node_props['Value'] = 'not-found'
                except (TypeError, KeyError):
                    node_props['Value'] = 'not-found'
                check = True

        count += 1

        updated_props = {node_props['Property']: node_props['Value']}
        # print(f"{node_props['Name']}: {node_props['Value']}")
        print(f"{count}/{total} complete", end='\r')
        sw.change_custom_properties(node_props['Uri'], updated_props)


def managed_roles(end_point, chef):
    """Pull down list of specified roles for use with loader"""
    tool_bag = Tools()
    save_path = "data/managed_roles.csv"
    patching_role = []
    empty_role = []
    response = chef.chef_get(end_point)
    for k in response.keys():
        run_list = (chef.chef_get(end_point, node=k))['run_list']
        run_list = [cleaner(item) for item in run_list]
        if 'chef-client' in run_list:
            patching_role.append(k)
    print(patching_role)
    print(empty_role)

    tool_bag.text_writer(save_path, patching_role)


def main():
    """Runs the loader"""
    # Set paths
    auth_path = "data/sw_access.txt"

    # Define tools
    tool_bag = Tools()

    # Initialize SolarWinds and Chef objects
    sw = SolarWindsInterface(auth_path)
    chef = ChefAPI()

    # Set query string
    query_str = """SELECT n.NodeName, n.NodeID, n.Uri, n.Agent.AgentID
                   FROM Orion.Nodes n
                   WHERE n.Agent.AgentID is not null"""

    query_results = sw.query(query_str)
    nodes = query_results['results']

    loader_menu(chef, sw, tool_bag, nodes)

    print("Exit")


if __name__ == "__main__":
    main()
