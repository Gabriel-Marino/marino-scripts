import argparse
import ctypes
import os
import platform
import psutil
import shutil
import subprocess

#! I DID THIS AS A STUDY PROJECT, THE CODE LOOK TO WORK BUT I DON'T HAVE WAYS TO ENSURE IT IS WORKING

class InputHandler:

    SUPPORTED_SYSTEM = ('Windows', 'Linux')

    def get_parser(self) -> argparse.ArgumentParser:

        parser = argparse.ArgumentParser(
            prog=os.path.basename(__file__),
            usage="%(prog)s [options]",
            description="",
            epilog=""
        )

        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument("--dll", metavar='FILE', help=f'Compile the input file as a Windows DLL')
        group.add_argument("--so" , metavar='FILE', help=f'Compile the input file as a Linux SO')

        parser.add_argument("--entry", type=str, default=ProcessHandler.DEFAULT_ENTRY_POINT, help=f'Custom entry point function. Default: {ProcessHandler.DEFAULT_ENTRY_POINT}')
        parser.add_argument("--target", type=str, help=f'Target process to inject the DLL or the SO into', required=True)
        parser.add_argument("--verbose", action='store_true', help='Enable verbose output')

        return parser

class ProcessHandler(InputHandler):

    DEFAULT_ENTRY_POINT = 'DllMain'
    SUPPORTED_TYPES = ('.s', '.c', '.cpp')

    def __init__(self) -> None:
        self.entry_point = self.DEFAULT_ENTRY_POINT

    def set(self, entry_point) -> None:
        self.entry_point = entry_point

    def compile(self, input_file: str, is_dll: bool = False, is_so: bool = False) -> str:

        if shutil.which('gcc') is None:
            raise RuntimeError('GCC compiler not found. Please install GCC and ensure it is in your PATH')

        if not os.path.isfile(input_file):
            raise FileNotFoundError(f'Input file not found: {input_file}')
        
        _, ext = os.path.splitext(input_file)
        if ext.lower() not in self.SUPPORTED_TYPES:
            raise ValueError(f'File type not supported. Supported types: {self.SUPPORTED_TYPES}')

        system = platform.system()
        windows, linux = self.SUPPORTED_SYSTEM
        if is_dll and system != windows:
            raise RuntimeError('DLL generation is only supported on Windows.')

        elif is_so and system != linux:
            raise RuntimeError('SO generation is only supported on Linux.')

        elif system not in self.SUPPORTED_SYSTEM:
            raise NotImplementedError(f'OS not supported: {system}.')

        base_name = os.path.splitext(os.path.basename(input_file))[0]
        output_file = f'{base_name}.dll' if is_dll else f'{base_name}.so'

        cmd = ['gcc', '-shared', '-o', output_file, input_file]

        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            return os.path.abspath(output_file)

        except subprocess.CalledProcessError as e:
            raise RuntimeError(f'Compilation failed.\nReturn code: {e.returncode}\nstdout: {e.stdout}\nstderr: {e.stderr}')

        except Exception as e:
            raise RuntimeError(f'An unexpected error occurred during compilation: {e}')

    def execute(self, input_file) -> None:

        windows = self.SUPPORTED_SYSTEM[0]
        system = platform.system()
        base_name = os.path.splitext(os.path.basename(input_file))[0]
        libname = f'{base_name}.dll' if system == windows else f'{base_name}.so'

        if not os.path.isfile(libname):
            raise FileNotFoundError(f'Compiled library not found: {libname}')

        try:
            lib = ctypes.CDLL(f'./{libname}')
            if hasattr(lib, self.entry_point):
                getattr(lib, self.entry_point)()

            else:
                raise AttributeError(f"Function '{self.entry_point}' not found in {libname}. Expected an entry point called '{self.entry_point}'")

        except Exception as e:
            print(f'An exception occurred: {e}')

    def inject(self, path: str, pid: int) -> None:

        path = os.path.abspath(path)

        system = platform.system()
        windows, linux = self.SUPPORTED_SYSTEM
        if system == windows:
            import ctypes.wintypes as wt

            K32 = ctypes.WinDLL('kernel32', use_last_error=True)

            INFINITY = 0xFFFFFFFF
            MEM_COMMIT = 0x1000
            PROCESS_ALL_ACCESS = 0x1F0FFF
            PAGE_EXECUTE_READWRITE = 0x40
            WAIT_OBJECT_0 = 0x00000000

            K32.OpenProcess.argtypes = [wt.DWORD, wt.BOOL, wt.DWORD]
            K32.OpenProcess.restype = wt.HANDLE
            handle = K32.OpenProcess(PROCESS_ALL_ACCESS, False, pid)
            if not handle:
                raise ctypes.WinError()

            path_bytes = ctypes.create_string_buffer(path.encode('utf-8'))
            path_size = ctypes.sizeof(path_bytes)
            K32.VirtualAllocEx.argtypes = [wt.HANDLE, ctypes.c_void_p, ctypes.c_size_t, wt.DWORD, wt.DWORD]
            K32.VirtualAllocEx.restype = ctypes.c_void_p
            arg_addr = K32.VirtualAllocEx(handle, 0, path_size, MEM_COMMIT, PAGE_EXECUTE_READWRITE)
            if not arg_addr:
                raise ctypes.WinError()

            written = ctypes.c_size_t(0)
            K32.WriteProcessMemory.argtypes = [wt.HANDLE, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]
            K32.WriteProcessMemory.restype = wt.BOOL
            res = K32.WriteProcessMemory(handle, arg_addr, path_bytes, path_size, ctypes.byref(written))
            if not res:
                raise ctypes.WinError()
            elif written.value != path_size:
                raise RuntimeError(f'Partial write: expected {path_size} bytes, wrote {written.value}')

            K32.GetModuleHandleA.argtypes = [ctypes.c_char_p]
            K32.GetModuleHandleA.restype = wt.HMODULE
            h_kernel32 = K32.GetModuleHandleA(b'kernel32.dll')
            K32.GetProcAddress.argtypes = [wt.HMODULE, ctypes.c_char_p]
            K32.GetProcAddress.restype = ctypes.c_void_p
            load_lib = K32.GetProcAddress(h_kernel32, b'LoadLibraryA')
            if not load_lib:
                raise ctypes.WinError()

            thread_id = ctypes.c_ulong(0)
            K32.CreateRemoteThread.restype = wt.HANDLE
            K32.CreateRemoteThread.argtypes = [wt.HANDLE, ctypes.c_void_p, ctypes.c_size_t, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_ulong, ctypes.POINTER(ctypes.c_ulong)]
            thread_handle = K32.CreateRemoteThread(handle, None, 0, load_lib, arg_addr, 0, ctypes.byref(thread_id))
            if not thread_handle:
                raise ctypes.WinError()

            K32.WaitForSingleObject.argtypes = [wt.HANDLE, wt.DWORD]
            K32.WaitForSingleObject.restype = wt.DWORD
            result = K32.WaitForSingleObject(thread_handle, INFINITY)
            if result != WAIT_OBJECT_0:
                raise ctypes.WinError()

            K32.CloseHandle.argtypes = [wt.HANDLE]
            K32.CloseHandle.restype = wt.BOOL
            K32.CloseHandle(thread_handle)
            K32.CloseHandle(handle)

        elif system == linux:

            raise NotImplementedError('Injection in Linux is yet to be implemented')

        else:
            raise NotImplementedError(f'{system} is not supported')

    def is_process_running(self, process: str) -> bool:

        for proc in psutil.process_iter(['name']):
            proc_name = proc.info['name']
            try:
                if proc_name and proc_name.lower() == process.lower():
                    return True

            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        return False

    def get_base_address(self, process: str) -> tuple[int, str]:

        pid = None
        for proc in psutil.process_iter(['pid', 'name']):
            if proc.info['name'].lower() == process.lower():
                pid = proc.info['pid']
                break

        if pid is None:
            raise RuntimeError(f'Process not found: {process}.')

        system = platform.system()
        windows, linux = self.SUPPORTED_SYSTEM
        if system == windows:

            import ctypes.wintypes as wt

            K32 = ctypes.WinDLL('kernel32', use_last_error=True)
            OPENPROCESS = K32.OpenProcess
            OPENPROCESS.restype = wt.HANDLE

            PSAPI = ctypes.windll.psapi
            ENUMPROCESSMODULES = PSAPI.EnumProcessModules

            PROCESS_QUERY_INFO = 0x0400
            PROCESS_VM_READ = 0x0010

            h_process = OPENPROCESS(PROCESS_QUERY_INFO | PROCESS_VM_READ, False, pid)
            if not h_process:
                raise RuntimeError(f"Failed to open process '{process}' (PID: {pid})")
            
            h_module = ctypes.c_void_p()
            if not ENUMPROCESSMODULES(h_process, ctypes.byref(h_module), ctypes.sizeof(h_module), ctypes.byref(ctypes.c_ulong())):
                raise RuntimeError('Failed to enumerate modules.')
            
            return pid, hex(h_module.value)

        elif system == linux:
            with open(f'/proc/{pid}/maps', 'r') as f:
                for line in f:
                    if 'r-xp' in line and not line.startswith('00'):
                        return pid, '0x' + line.split('-')[0]
            
            raise RuntimeError(f'Could not determine base address of {process}')

        else:
            raise NotImplementedError(f'{system} is not supported.')

def main() -> None:

    try:
        processes = ProcessHandler()
        input_handler = InputHandler()
        parser = input_handler.get_parser()
        args = parser.parse_args()
        processes.set(entry_point=args.entry)

        if not processes.is_process_running(args.target):
            raise RuntimeError(f'Target program is not running: {args.target}')

        target_pid, target_base_addr = processes.get_base_address(args.target)
        if args.verbose:
            print(f'The target {args.target} is allocated in {target_base_addr} with pid {target_pid}')

        if args.dll:
            dll_path = processes.compile(args.dll, is_dll=True)
            processes.inject(dll_path, target_pid)

        elif args.so:
            so_path = processes.compile(args.so, is_so=True)
            processes.inject(so_path, target_pid)

    except Exception as e:
        print(f'An exception occurred: {e}')
        raise

if __name__ == "__main__":
    main()
