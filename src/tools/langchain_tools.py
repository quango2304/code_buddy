from pathlib import Path

from langchain_community.agent_toolkits import FileManagementToolkit

# Root directory for file operations (where python command is executed)
ROOT_DIR = Path.cwd()

def get_langchain_tools() -> list:
    """Get file management tools from LangChain.
            CopyFileTool,
            DeleteFileTool,
            FileSearchTool,
            MoveFileTool,
            ReadFileTool,
            WriteFileTool, <- write a new file
            ListDirectoryTool,
    """
    toolkit = FileManagementToolkit(
        root_dir=str(ROOT_DIR),
        selected_tools=[
            "copy_file",
            "file_delete",
            "file_search",
            "move_file",
            "read_file",
            "write_file",
            "list_directory",
        ],
    )
    return toolkit.get_tools()
