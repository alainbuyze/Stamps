"""Test colnect_api module imports."""
try:
    from src.colnect_api import CDPSession, ColnectActions, create_colnect_session, create_colnect_actions
    print('All imports successful!')
    print(f'  CDPSession: {CDPSession}')
    print(f'  ColnectActions: {ColnectActions}')
    print(f'  create_colnect_session: {create_colnect_session}')
    print(f'  create_colnect_actions: {create_colnect_actions}')
except Exception as e:
    import traceback
    traceback.print_exc()
    print(f'Error: {e}')
    exit(1)
