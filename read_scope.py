from headers.rigol_ds1102e import RigolDS1102e

# Initialize connection
scope = RigolDS1102e()

# Set capture settings
scope.active_channel = 2
scope.voltage_scale = 0.5 # V/div
scope.voltage_offset = 0
scope.time_scale = 1e-3 # s/div
scope.time_offset = 0

# Set trigger settings
scope.trigger_direction = 'rising'
scope.trigger_source = 'ch1'
scope.trigger_level = 0.2 # V

# Display configuration
print(scope)

scope.quick_plot()

scope.stop()
