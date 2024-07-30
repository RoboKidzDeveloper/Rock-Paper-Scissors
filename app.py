from flask import Flask, render_template, Response, jsonify
import cv2
import mediapipe as mp
import requests

app = Flask(__name__)

# Initialize MediaPipe Hands.
mp_draw = mp.solutions.drawing_utils
mp_hands = mp.solutions.hands.Hands(min_detection_confidence=0.5, min_tracking_confidence=0.5)

# Coordinates of the square
square_x1, square_y1 = 210, 100
square_x2, square_y2 = square_x1 + 250, square_y1 + 180

server_ip = "192.168.4.1"  # Replace with the IP address of your Arduino server

video = None
is_running = False

def gen_frames():
    global video, is_running
    while is_running:
        success, frame = video.read()
        if not success:
            break
        else:
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = mp_hands.process(frame_rgb)
            lmList = []

            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    if hand_landmarks.landmark[mp.solutions.hands.HandLandmark.WRIST].x < hand_landmarks.landmark[mp.solutions.hands.HandLandmark.THUMB_TIP].x:
                        for id, lm in enumerate(hand_landmarks.landmark):
                            h, w, c = frame.shape
                            cx, cy = int(lm.x * w), int(lm.y * h)
                            lmList.append([id, cx, cy])
                        mp_draw.draw_landmarks(frame, hand_landmarks, mp.solutions.hands.HAND_CONNECTIONS)
                        break

            fingers = []
            if lmList:
                if lmList[4][1] > lmList[3][1]:
                    fingers.append(1)
                else:
                    fingers.append(0)

                for id in [8, 12, 16, 20]:
                    if lmList[id][2] < lmList[id - 2][2]:
                        fingers.append(1)
                    else:
                        fingers.append(0)

                total_fingers = fingers.count(1)
            else:
                total_fingers = 0

            cv2.rectangle(frame, (20, 300), (270, 425), (0, 255, 0), cv2.FILLED)
            cv2.putText(frame, str(total_fingers), (45, 375), cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 0, 0), 5)

            cv2.rectangle(frame, (square_x1, square_y1), (square_x2, square_y2), (155, 0, 0), 2)
            cv2.putText(frame, "Place your hand here", (square_x1, square_y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)

            hand_in_square = any(square_x1 < lm[1] < square_x2 and square_y1 < lm[2] < square_y2 for lm in lmList)
            if hand_in_square:
                requests.get(f"http://{server_ip}/data/?sensor_reading={{\"sensor0_reading\":{total_fingers}}}")
            else:
                requests.get(f"http://{server_ip}/data/?sensor_reading={{\"sensor0_reading\":0}}")

            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')



@app.route('/')
def index():
    return render_template('index.html')

@app.route('/start', methods=['POST'])
def start():
    global video, is_running
    if not is_running:
        video = cv2.VideoCapture(0)
        is_running = True
    return jsonify({'status': 'started'})

@app.route('/stop', methods=['POST'])
def stop():
    global video, is_running
    if is_running:
        is_running = False
        video.release()
        video = None
    return jsonify({'status': 'stopped'})

@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(debug=True)
