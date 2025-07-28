import os

def list_files_recursive(path, indent=0):
    try:
        for entry in os.listdir(path):
            full_path = os.path.join(path, entry)
            print("  " * indent + "|-- " + entry)
            if os.path.isdir(full_path):
                list_files_recursive(full_path, indent + 1)
    except PermissionError:
        print("  " * indent + "|-- [접근 불가]")

if __name__ == "__main__":
    base_path = r"C:\woohyun\AJIN-12th-project"
    print(f"Directory listing for {base_path}:")
    list_files_recursive(base_path)

