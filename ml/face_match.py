from deepface import DeepFace
import os

def find_match(search_image_path, missing_folder_path):
    """
    Compare search image with all images in missing folder.
    Returns matched image path if found.
    """

    for filename in os.listdir(missing_folder_path):
        missing_image_path = os.path.join(missing_folder_path, filename)

        try:
            result = DeepFace.verify(
                img1_path=search_image_path,
                img2_path=missing_image_path,
                enforce_detection=False
            )

            if result["verified"]:
                return missing_image_path

        except Exception as e:
            print("Error comparing:", e)

    return None