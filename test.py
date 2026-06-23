# Testing file - checking if extract_ram works correctly

from employee_ram import extract_ram

print("Starting tests...")
print("")

# Test 1 - The original 3 employees
print("Test 1:")
data1 = {
    "Raju": {"HW": "Laptop", "Config": {"RAM": 16, "CPU": 8}},
    "Ramu": {"HW": "Laptop", "Config": {"RAM": 12, "CPU": 8}},
    "Gopi": {"HW": "Laptop", "Config": {"RAM": 8, "CPU": 8}}
}
extract_ram(data1)
print("---")

# Test 2 - Only one employee
print("Test 2:")
data2 = {
    "Sita": {"HW": "Desktop", "Config": {"RAM": 32, "CPU": 16}}
}
extract_ram(data2)
print("---")

# Test 3 - Two employees
print("Test 3:")
data3 = {
    "Ram": {"HW": "Laptop", "Config": {"RAM": 8, "CPU": 4}},
    "Lakshman": {"HW": "Desktop", "Config": {"RAM": 16, "CPU": 8}}
}
extract_ram(data3)
print("---")

# Test 4 - Empty dictionary
print("Test 4:")
data4 = {}
extract_ram(data4)
print("(Nothing should print above for empty data)")
print("---")

# Test 5 - Four employees with different RAM
print("Test 5:")
data5 = {
    "John": {"HW": "Laptop", "Config": {"RAM": 4, "CPU": 2}},
    "Jane": {"HW": "Laptop", "Config": {"RAM": 8, "CPU": 4}},
    "Jack": {"HW": "Desktop", "Config": {"RAM": 16, "CPU": 8}},
    "Jill": {"HW": "Desktop", "Config": {"RAM": 32, "CPU": 16}}
}
extract_ram(data5)
print("---")

print("All tests done")