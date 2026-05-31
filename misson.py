import asyncio
from mavsdk import System
from mavsdk.mission import MissionItem, MissionPlan
import cv2
from ultralytics import YOLO


model = YOLO("yolov8n.pt")

cap = cv2.VideoCapture("drone_video2.mp4")



async def check_connected(drone):
    async for state in drone.core.connection_state():
        if state.is_connected:
            print("-- Drone Connected Successfully!")
            break

async def check_armed(drone):
    async for armed in drone.telemetry.armed():
        if armed:
            break
async def check_takeoff(drone):
    async for state in drone.telemetry.landed_state():
        if state == state.IN_AIR:
            
            break

async def main():

    
    drone = System()

    print("Connecting to drone...")

    await drone.connect(system_address="udp://:14540")

    
    await check_connected(drone)

    
    home = await anext(drone.telemetry.home())

    lat = home.latitude_deg
    lon = home.longitude_deg

    print(f"Home Location: {lat}, {lon}")

    
    altitude = 15.0

    
    mission_items = [

        # Point 1
        MissionItem(
            lat,lon + 0.0002, altitude,15.0,
            True,
            float('nan'),
            float('nan'),
            MissionItem.CameraAction.NONE, float('nan'),float('nan'),float('nan'),float('nan'),float('nan'),MissionItem.VehicleAction.NONE
        ),

        # Point 2
        MissionItem(
            lat,lon + 0.00020,
            altitude,15.0,True,
            float('nan'),
            float('nan'),
            MissionItem.CameraAction.NONE,
            float('nan'),float('nan'), float('nan'),float('nan'),float('nan'),MissionItem.VehicleAction.NONE
        )
    ]

    
    mission_plan = MissionPlan(mission_items)

   
    print("Uploading mission...")

    await drone.mission.upload_mission(mission_plan)

    
    print("Arming drone...")

    await drone.action.arm()
    await check_armed(drone)

   
    print("Taking off...")

    await drone.action.takeoff()
    await check_takeoff(drone)
    await asyncio.sleep(3)

    
    print("Starting mission...")

    await drone.mission.start_mission()

    print("Mission started successfully!")

    
    print("AI Detection Started...")

    detected = False

    while True:

        # Read video frame
        success, frame = cap.read()

        
        if not success:
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            continue

        
        frame = cv2.resize(frame, (640, 480))

        
        results = model(
            frame,
            conf=0.25,
            classes=[7],   
            verbose=False
        )[0]

        
        annotated_frame = results.plot()

        
        if len(results.boxes) > 0:

            cv2.putText(
                annotated_frame,
                "TRUCK DETECTED",
                (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 0, 255),
                2
            )

            # Print once only
            if not detected:

                detected = True

                print("================================")
                print("TARGET DETECTED SUCCESSFULLY!")
                print("================================")

        else:
            detected = False

       
        cv2.imshow("Drone AI View", annotated_frame)

        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

        
    

    
    print("Landing drone...")

    await drone.action.land()

    await asyncio.sleep(5)

   
    cap.release()

    cv2.destroyAllWindows()

    print("Program finished successfully!")



if __name__ == "__main__":
    asyncio.run(main())