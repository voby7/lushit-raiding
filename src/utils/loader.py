import os
import sys
import importlib
import traceback
import colorama

debug_mode = os.getenv("DEBUG_MODE") == "True"

async def load_cogs(bot, directory: str = None):
    """
    Automatically loads all cogs inside the given directory.
    Each cog must contain an async setup(bot) function.
    """

    # Resolve directory relative to THIS file, not cwd
    if directory is None:
        directory = os.path.join(os.path.dirname(__file__), "..", "cogs")

    directory = os.path.abspath(directory)

    if not os.path.isdir(directory):
        if debug_mode:
            print(colorama.Fore.RED + f"[CogLoader] Directory does not exist: {directory}" + colorama.Style.RESET_ALL)
        return

    # Compute project root (folder containing src/)
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

    # Force project root into sys.path
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    # Build import prefix (e.g., src.cogs)
    rel_path = os.path.relpath(directory, project_root)
    import_prefix = rel_path.replace(os.sep, ".")

    if debug_mode == "True":
        print(colorama.Fore.CYAN + f"[CogLoader] Project root: {project_root}" + colorama.Style.RESET_ALL)
        print(colorama.Fore.CYAN + f"[CogLoader] Import prefix: {import_prefix}" + colorama.Style.RESET_ALL)

    for filename in os.listdir(directory):
        if not filename.endswith(".py"):
            continue
        if filename.startswith("_"):
            continue

        module_name = filename[:-3]
        full_import = f"{import_prefix}.{module_name}"

        try:
            if full_import in sys.modules:
                module = importlib.reload(sys.modules[full_import])
            else:
                module = importlib.import_module(full_import)

            setup_func = getattr(module, "setup", None)
            if setup_func is None:
                if debug_mode == "True":
                    print(colorama.Fore.YELLOW + f"[CogLoader] Skipped {module_name}: no setup()" + colorama.Style.RESET_ALL)
                continue

            await setup_func(bot)

            if debug_mode == "True":
                print(colorama.Fore.GREEN + f"[CogLoader] Loaded cog: {module_name}" + colorama.Style.RESET_ALL)

        except Exception:
            print(colorama.Fore.RED + f"[CogLoader] Failed to load {module_name}" + colorama.Style.RESET_ALL)
            print(colorama.Fore.RED + traceback.format_exc() + colorama.Style.RESET_ALL)
