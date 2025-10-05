def get_config_value(key: str, default=None):
    """
    Fetch a config value from the system_config table. Returns default if not found or on error.
    """
    from database.db_cofig import supabase
    response = supabase.table('system_config').select('value').eq('key', key).single().execute()
    if hasattr(response, 'error') and response.error:
        return default
    if response.data and 'value' in response.data:
        try:
            return int(response.data['value'])
        except ValueError:
            return response.data['value']
    return default
