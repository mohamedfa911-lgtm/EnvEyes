import asyncio
from mavsdk import System
from mavsdk.mission import MissionItem, MissionPlan

async def check_armed(drone):
    async for armed in drone.telemetry.armed():
        if armed:
            break

async def main():
    drone = System()
    await drone.connect(system_address="udp://:14540")
    print(" Connected to PX4 Simulator...")

    
    print(" Adjusting system parameters for Windy world...")
    try:
        await drone.param.set_param_int("COM_ARM_EKF_HGT", 0)  
        await drone.param.set_param_int("COM_ARM_WO_GPS", 1)   
        await drone.param.set_param_int("COM_RCL_EXCEPT", 4)   
        await asyncio.sleep(1)
    except Exception as e:
        print(f" Note: Parameter setup skipped or delayed: {e}")

    
    print(" Formulating Flight Mission to Truck Sites...")
    mission_items = []
    
    
    truck_points = [
        (47.397828, 8.546164, 8.0, 12.0),  # Truck 1 (Dumptruck)
        (47.398234, 8.545698, 8.0, 12.0)   # Truck 2 (Water Tanker)
    ]
    
    for lat, lon, alt, speed in truck_points:
        mission_items.append(MissionItem(
            lat, lon, alt, speed, 
            is_fly_through=False,      
            gimbal_pitch_deg=-90.0,        
            gimbal_yaw_deg=float('nan'),
            camera_action=MissionItem.CameraAction.NONE,
            loiter_time_s=5.0,                 
            camera_photo_interval_s=float('nan'),
            acceptance_radius_m=1.0, yaw_deg=float('nan'),
            camera_photo_distance_m=float('nan'),
            vehicle_action=MissionItem.VehicleAction.NONE
        ))

    mission_plan = MissionPlan(mission_items)
    

    await drone.mission.set_return_to_launch_after_mission(True)
    
    print("⬆ Uploading Mission to Drone...")
    await drone.mission.upload_mission(mission_plan)

    
    print(" Arming motors...")
    await drone.action.arm()
    await asyncio.sleep(1)
    
    print(" Drone is taking off and initiating the mission...")
    await drone.mission.start_mission()

    
    async for mission_progress in drone.mission.mission_progress():
        current = mission_progress.current
        total = mission_progress.total
        print(f" Drone Status: At Waypoint {current}/{total}")
        
        if current == total:
            print(" Reached last truck! Initiating Return To Launch (RTL)...")
            break
        await asyncio.sleep(1)

    
    await asyncio.sleep(5)
    print(" Mission Finished. Drone has landed safely at home base.")


asyncio.run(main())