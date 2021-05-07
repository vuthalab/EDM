from headers.rigol_ds1102e import RigolDS1102e

# Initialize connection
scope = RigolDS1102e()
print(scope)

scope.quick_plot()

scope.active_channel = 2
scope.quick_plot()

scope.stop()
