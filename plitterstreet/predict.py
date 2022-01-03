"""
This is to make predicitons to identify plastic litter in the images
Supported models:
    AutoML --> tf edge
    detectron2 --> faster-r-cnn, works in colab easily, detectron2 installation needed in local
    darknet --> yolov4, works in colab easily, darknet installation is needed in local
"""

import cv2
import tensorflow as tf
import tqdm

def draw_boxes_on_image(image, boxes, classes, scores, use_normalized_coordinates=True, min_score_thresh=.2):
    assert len(boxes) == len(scores) ==len(classes)
    for i in range(len(boxes)):
        box = boxes[i]
        category = classes[i].decode()
        score = scores[i]
        if score >= min_score_thresh:
          h,w,_ = image.shape
          y1 = int(box[0]*h)
          x1 = int(box[1]*w)
          y2 = int(box[2]*h)
          x2 = int(box[3]*w)
          image = cv2.rectangle(image, (x1, y1), (x2, y2), (0,255,255), 2)
          cv2.putText(image, category+':'+str(round(score,2)), (x1, y1-5), cv2.FONT_HERSHEY_SIMPLEX, 0.3, (0,255,255), 2)
    return image

class EdgePredictor():
    def __init__(self, model_path):
        loaded = tf.saved_model.load(export_dir=model_path)
        self.infer = loaded.signatures["serving_default"]
        self.ready = True

    def predict(self, path):
        if type(path) == str:
            img = cv2.imread(path)
            flag, bts = cv2.imencode('.jpg', img)
            input = [bts[:,0].tobytes()]
            output = self.infer(key=tf.constant('something_unique'), image_bytes=tf.constant(input))
        else:
            # change condition to check image
            # print(path.shape)
            flag, bts = cv2.imencode('.jpg', path)
            input = [bts.tobytes()]
            output = self.infer(key=tf.constant('something_unique'), image_bytes=tf.constant(input))
        return output
    
    def frame_from_video(self, video):
        while video.isOpened():
            ret, frame = video.read()
            if ret:
                yield frame
            else:
                break 

    def video_inference(self, video, vid_out_path):
        if type(video) == str:
            vid_cap = cv2.VideoCapture(video)
        else:
            vid_cap = video
        num_frames = int(vid_cap.get(cv2.CAP_PROP_FRAME_COUNT))
        # print(num_frames)
        fps = int(vid_cap.get(cv2.CAP_PROP_FPS))
        width = int(vid_cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(vid_cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        fourcc = cv2.VideoWriter_fourcc('M','J','P','G')
        vid_out = cv2.VideoWriter(vid_out_path, fourcc, fps, (width,  height))

        for frame in tqdm.tqdm(self.frame_from_video(vid_cap), total=num_frames):
            output = self.predict(frame)
            classes = output['detection_classes_as_text'].numpy()[0]
            scores = output['detection_scores'].numpy()[0]
            boxes = output['detection_boxes'].numpy()[0]
            result = draw_boxes_on_image(image=frame, boxes=boxes, classes=classes, scores=scores, use_normalized_coordinates=True, min_score_thresh=.4)
            cv2.imwrite('/content/data/result.jpg', result)
            vid_out.write(result)
        vid_cap.release()
        vid_out.release()