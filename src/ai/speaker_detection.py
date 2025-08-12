from pathlib import Path

import cv2
import mediapipe as mp
import numpy as np

mp_face_detection = mp.solutions.face_detection
mp_face_mesh = mp.solutions.face_mesh


def convert_relative_bbox_to_absolute_bbox(
    frame: np.ndarray, relative_bbox: tuple[float, float, float, float]
) -> tuple[int, int, int, int]:
    """
    Converts a relative bounding box (0-1 range) to absolute pixel coordinates.

    Args:
        frame (np.ndarray): Original image frame.
        relative_bbox (mediapipe.framework.formats.location_data_pb2.LocationData.RelativeBoundingBox): Relative bbox.

    Returns:
        Tuple[int, int, int, int]: (x, y, width, height) in absolute pixel values.
    """
    h, w, _ = frame.shape
    x1 = int(relative_bbox.xmin * w)
    y1 = int(relative_bbox.ymin * h)
    bw = int(relative_bbox.width * w)
    bh = int(relative_bbox.height * h)

    return (x1, y1, bw, bh)


def crop_frame_on_face(
    frame: np.ndarray, face_bbox: tuple[int, int, int, int]
) -> np.ndarray:
    return frame[
        face_bbox[1] : face_bbox[1] + face_bbox[3],
        face_bbox[0] : face_bbox[0] + face_bbox[2],
    ]


def calculate_lips_distance(
    face_landmarks, face_bbox: tuple[int, int, int, int]
) -> float:
    """
    Calculates the Euclidean distance between the upper and lower lips using facial landmarks.

    Args:
        landmarks (mediapipe.framework.formats.landmark_pb2.NormalizedLandmarkList): Face landmarks.
        bbox (Tuple[int, int, int, int]): Bounding box (x, y, w, h) used to scale landmarks.

    Returns:
        float: Distance between upper and lower lip landmarks.
    """

    UPPER_LIP_IDX = 13
    LOWER_LIP_IDX = 14

    top_lip = np.array(
        [
            face_landmarks.landmark[UPPER_LIP_IDX].x * face_bbox[2],
            face_landmarks.landmark[UPPER_LIP_IDX].y * face_bbox[3],
        ]
    )
    bottom_lip = np.array(
        [
            face_landmarks.landmark[LOWER_LIP_IDX].x * face_bbox[2],
            face_landmarks.landmark[LOWER_LIP_IDX].y * face_bbox[3],
        ]
    )
    return np.linalg.norm(top_lip - bottom_lip)


def detect_active_speaker(
    video_path: Path, frame_skip_interval: int
) -> list[tuple[int, int, int, int]]:
    """
    Detects the position of the most likely active speaker in a video based on lip movement.

    Args:
        video_path (str): Path to the input video file.
        frame_skip_interval (int): Number of frames to skip between evaluations (for performance).

    Returns:
        List of bounding boxes (x, y, width, height) for the active speaker per sampled frame.
    """
    cap = cv2.VideoCapture(video_path)
    frame_index = 0
    speaker_positions = []

    with mp_face_detection.FaceDetection(
        model_selection=1, min_detection_confidence=0.5
    ) as face_detector, mp_face_mesh.FaceMesh(
        static_image_mode=True, max_num_faces=1, refine_landmarks=False
    ) as face_mesh:

        while cap.isOpened():
            # Read every `frame_skip_interval`-th frame
            if frame_index % frame_skip_interval == 0:
                success, frame = cap.read()
                if not success:
                    break

                # Convert BGR image to RGB for MediaPipe processing
                image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                max_lip_distance = -1
                detected_speaker_bbox = None

                face_results = face_detector.process(image_rgb)

                # If multiple faces are detected, determine the one with most lip movement
                if face_results.detections and len(face_results.detections) > 1:
                    for detection in face_results.detections:
                        face_bbox = convert_relative_bbox_to_absolute_bbox(
                            image_rgb, detection.location_data.relative_bounding_box
                        )
                        cropped_face = crop_frame_on_face(image_rgb, face_bbox)

                        if cropped_face.size == 0:
                            continue

                        mesh_result = face_mesh.process(cropped_face)
                        if mesh_result.multi_face_landmarks:
                            landmarks = mesh_result.multi_face_landmarks[0]
                            lip_distance = calculate_lips_distance(landmarks, face_bbox)

                            if lip_distance > max_lip_distance:
                                max_lip_distance = lip_distance
                                detected_speaker_bbox = face_bbox

                # If only one face is detected, assume it's the speaker
                elif face_results.detections and len(face_results.detections) == 1:
                    detection = face_results.detections[0]
                    detected_speaker_bbox = convert_relative_bbox_to_absolute_bbox(
                        image_rgb, detection.location_data.relative_bounding_box
                    )

                if detected_speaker_bbox:
                    speaker_positions.append(detected_speaker_bbox)

            frame_index += 1

    cap.release()
    return speaker_positions


def get_average_speaker_position(
    video_path: Path, frame_skip_interval: int
) -> tuple[int, int, int, int] | None:
    """
    Returns the bounding box of the active speaker whose center x-position is the median.

    Args:
        video_path (Path): Path to the input video file.
        frame_skip_interval (int): Number of frames to skip between evaluations.

    Returns:
        tuple[int, int, int, int] or None: Bounding box (x, y, width, height) corresponding to
                                           the median center x-position, or None if no speaker was detected.
    """
    active_speaker_bbox_list = detect_active_speaker(video_path, frame_skip_interval)

    if len(active_speaker_bbox_list) == 0:
        return None

    # Compute center x for each bbox
    center_x_list = [bbox[0] + bbox[2] // 2 for bbox in active_speaker_bbox_list]

    # Get index of median center x by sorting and finding the middle index
    sorted_indices = sorted(range(len(center_x_list)), key=lambda i: center_x_list[i])
    median_index = sorted_indices[len(sorted_indices) // 2]

    return active_speaker_bbox_list[median_index]


def bbox_overlap(
    bbox1: tuple[int, int, int, int], bbox2: tuple[int, int, int, int]
) -> bool:
    """
    Checks if two bounding boxes overlap horizontally.
    Only checks x-axis overlap for cropping purposes.
    """
    x1, _, w1, _ = bbox1
    x2, _, w2, _ = bbox2
    return not (x1 + w1 < x2 or x2 + w2 < x1)


def group_bboxes_by_overlap(bboxes: list[tuple[int, int, int, int]]) -> list[int]:
    """
    Groups successive bounding boxes based on horizontal overlap and assigns each group
    the median x-center value. This helps to get a smooth cropping when creating shorts

    Args:
        bboxes: List of bounding boxes (x, y, w, h)

    Returns:
        A list of x-center values (same length as input), where overlapping bbox groups
        share the same x-center crop.
    """
    group_centers = []
    current_group = []

    for bbox in bboxes:
        if bbox is None:
            # Finalize any ongoing group
            if current_group:
                centers = [b[0] + b[2] // 2 for b in current_group]
                median_center = int(np.median(centers))
                group_centers.extend([median_center] * len(current_group))
                current_group = []
            group_centers.append(None)
        else:
            if not current_group:
                current_group.append(bbox)
            else:
                if bbox_overlap(bbox, current_group[-1]):
                    current_group.append(bbox)
                else:
                    # Finalize current group
                    centers = [b[0] + b[2] // 2 for b in current_group]
                    median_center = int(np.median(centers))
                    group_centers.extend([median_center] * len(current_group))
                    current_group = [bbox]

    # Final group
    if current_group:
        centers = [b[0] + b[2] // 2 for b in current_group]
        median_center = int(np.median(centers))
        group_centers.extend([median_center] * len(current_group))

    return group_centers
