from __future__ import absolute_import

from billiard.compat import _winapi

from .case import Case, skip

WIN32_CONSTANTS = {
    'ERROR_ALREADY_EXISTS',
    'ERROR_PIPE_BUSY',
    'ERROR_PIPE_CONNECTED',
    'ERROR_SEM_TIMEOUT',
    'ERROR_MORE_DATA',
    'ERROR_BROKEN_PIPE',
    'ERROR_IO_PENDING',
    'ERROR_NETNAME_DELETED',
    'GENERIC_READ',
    'GENERIC_WRITE',
    'DUPLICATE_SAME_ACCESS',
    'DUPLICATE_CLOSE_SOURCE',
    'INFINITE',
    'NMPWAIT_WAIT_FOREVER',
    'OPEN_EXISTING',
    'PIPE_ACCESS_DUPLEX',
    'PIPE_ACCESS_INBOUND',
    'PIPE_READMODE_MESSAGE',
    'PIPE_TYPE_MESSAGE',
    'PIPE_UNLIMITED_INSTANCES',
    'PIPE_WAIT',
    'PROCESS_ALL_ACCESS',
    'PROCESS_DUP_HANDLE',
    'WAIT_OBJECT_0',
    'WAIT_ABANDONED_0',
    'WAIT_TIMEOUT',
    'FILE_FLAG_FIRST_PIPE_INSTANCE',
    'FILE_FLAG_OVERLAPPED',
}

WIN32_FUNCTIONS = {
    'CloseHandle',
    'GetLastError',
    'OpenProcess',
    'ExitProcess',
    'ConnectNamedPipe',
    'CreateFile',
    'WriteFile',
    'ReadFile',
    'CreateNamedPipe',
    'SetNamedPipeHandleState',
    'WaitNamedPipe',
    'PeekNamedPipe',
    'WaitForMultipleObjects',
    'WaitForSingleObject',
    'GetCurrentProcess',
    'GetExitCodeProcess',
    'TerminateProcess',
    'DuplicateHandle',
    'CreatePipe',
}


@skip.unless_win32()
class test_win32_module(Case):

    def test_constants(self):
        for const in WIN32_CONSTANTS:
            self.assertIsNotNone(getattr(_winapi, const))
        getattr(_winapi, 'NULL')

    def test_functions(self):
        getattr(_winapi, 'Overlapped')
        for fun in WIN32_FUNCTIONS:
            self.assertTrue(getattr(_winapi, fun))
