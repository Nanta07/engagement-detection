import cv2
import mediapipe as mp
import numpy as np
import joblib

# Load the trained SVM model and scaler
svm_model = joblib.load('svm_engagement_model_1.pkl')
scaler = joblib.load('scaler.pkl')

# Initialize Mediapipe Face Mesh
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(static_image_mode=False, max_num_faces=1, min_detection_confidence=0.5)

# Initialize Mediapipe Drawing
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles

# Start the webcam
cap = cv2.VideoCapture(0)

while cap.isOpened():
    success, frame = cap.read()
    if not success:
        break
    
    # Convert the frame to RGB
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    
    # Process the frame to detect facial landmarks
    result = face_mesh.process(frame_rgb)
    
    if result.multi_face_landmarks:
        # Get the landmarks for the first face detected
        landmarks = result.multi_face_landmarks[0].landmark
        
        # Extract the (x, y) coordinates of all landmarks and flatten them into a list
        h, w, _ = frame.shape  # Get frame dimensions
        flattened_landmarks = []
        face_coords = []  # Store (x, y) for drawing the bounding box

        for landmark in landmarks:
            x = int(landmark.x * w)
            y = int(landmark.y * h)
            flattened_landmarks.append(landmark.x)
            flattened_landmarks.append(landmark.y)
            face_coords.append((x, y))
        
        # Draw the bounding box around the face
        x_min = min([coord[0] for coord in face_coords])
        y_min = min([coord[1] for coord in face_coords])
        x_max = max([coord[0] for coord in face_coords])
        y_max = max([coord[1] for coord in face_coords])
        
        cv2.rectangle(frame, (x_min, y_min), (x_max, y_max), (0, 255, 0), 2)
        
        # Draw facial landmarks on the frame
        for coord in face_coords:
            cv2.circle(frame, coord, 1, (0, 255, 255), -1)

        # Convert the list of flattened landmarks to a numpy array and reshape
        flattened_landmarks = np.array(flattened_landmarks).reshape(1, -1)
        
        # Scale the landmarks using the same scaler used during training
        flattened_landmarks_scaled = scaler.transform(flattened_landmarks)
        
        # Predict engagement level using the SVM model
        prediction = svm_model.predict(flattened_landmarks_scaled)
        
        # Determine if the user is engaged or not engaged
        if prediction == 1:
            engagement_status = "Engaged"
        else:
            engagement_status = "Not Engaged"
        
        # Display the engagement status on the frame
        cv2.putText(frame, f"Status: {engagement_status}", (30, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    
    # Display the frame
    cv2.imshow('Engagement Detection', frame)
    
    # Press 'q' to exit
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release the webcam and close windows
cap.release()
cv2.destroyAllWindows()