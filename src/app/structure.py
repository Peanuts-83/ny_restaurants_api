import os

def print_package_structure(directory):
    """
    Method designed to display project structure.
    Just import this module in main.
    """
    # Print the current directory
    print(directory)

    # Iterate over the contents of the directory
    for item in os.listdir(directory):
        # Get the full path of the item
        item_path = os.path.join(directory, item)

        # If the item is a directory, recursively print its structure
        if os.path.isdir(item_path):
            print_package_structure(item_path)
        # If the item is a file, print its name
        elif os.path.isfile(item_path):
            print(f"  {item}")

# Specify the path to your project directory
project_directory = "./"

# Call the function to print the package structure
print_package_structure(project_directory)
