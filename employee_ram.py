
def extract_ram(data):
    """Extract RAM values from employee hardware configs"""
    if not data:
        print("No data provided")
        return
    
    print(f"\n{'Name':<20} {'HW Type':<15} {'RAM (GB)':<10}")
    print("-" * 50)
    
    for name, config in data.items():
        hw_type = config.get('HW', 'Unknown')
        ram = config.get('Config', {}).get('RAM', 'N/A')
        print(f"{name:<20} {hw_type:<15} {ram:<10}")
