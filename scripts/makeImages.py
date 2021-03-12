'''
converts video to frames and saves images by different interval, or overlap, etc
'''
import os
import cv2

class Video:
    def __init__(self, file_name):
        self.file_name = file_name
        self.base_name = os.path.basename(file_name)
        self.vidcap = cv2.VideoCapture(self.file_name) 
        success,image = self.vidcap.read()
        if not success:
            print("Can not read frames in the video!")
        else:
            print("Video is set and ready to make frames")
        self.vidcap.release()
    def byInterval(self, interval=1, out_path=''):
        vidcap = cv2.VideoCapture(self.file_name)
        success,image = vidcap.read()
        if success:
            if out_path=='':
                out_path = os.path.dirname(self.file_name)
            else:
                out_path = os.path.abspath(out_path)
            folder_name = os.path.splitext(self.base_name)[0]
            abs_folder_name = os.path.join(out_path, folder_name)
            try:
                if not os.path.exists(abs_folder_name):
                    os.mkdir(abs_folder_name) 
            except OSError as error: 
                print(error)

        count = 0
        while success:
            vidcap.set(cv2.CAP_PROP_POS_MSEC,(count*interval*1000))
            success,image = vidcap.read()
            cv2.imwrite(os.path.join(abs_folder_name, folder_name+'_'+str(count)+'.jpg'), image)
            count += 1
        vidcap.release()

    # To Do
    # def byTimestamp():
        # listTimestamp = []

    def overlap(self, cnt_th=1, qlt_th=0.7, out_path=''):
        vidcap = cv2.VideoCapture(self.file_name)
        # vidcap.set(cv2.CAP_PROP_POS_MSEC,(20000))
        success, frame1 = vidcap.read()
        if success:
            if out_path=='':
                out_path = os.path.dirname(self.file_name)
            else:
                out_path = os.path.abspath(out_path)
            folder_name = os.path.splitext(self.base_name)[0]
            abs_folder_name = os.path.join(out_path, folder_name)
            try:
                if not os.path.exists(abs_folder_name):
                    os.mkdir(abs_folder_name) 
            except OSError as error: 
                print(error)

        first_frame = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
        count = 0
        image_count = 0
        cv2.imwrite(os.path.join(abs_folder_name, folder_name+'_'+str(image_count)+'.jpg'), frame1)
        image_count += 1
        match_cnt1 = 100
        match_cnt2 = 100
        while(vidcap.isOpened()):
            count += 1
            success, frame2 = vidcap.read()

            if success == False:
                print('Unable to read next frame')
                continue
            second_frame = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)

            orb = cv2.ORB_create()
            kp1, kp_des1 = orb.detectAndCompute(first_frame, None)
            kp2, kp_des2 = orb.detectAndCompute(second_frame, None)
            kp_matcher = cv2.BFMatcher()
            kp_matched = kp_matcher.knnMatch(kp_des1, kp_des2, k=2)

            # Apply ratio test
            kp_matched_well = []
            for m,n in kp_matched:
                if m.distance < qlt_th*n.distance:
                    kp_matched_well.append(m)
        
            kp_matched_well_len = len(kp_matched_well)
        
            match_cnt1 = match_cnt2
            match_cnt2 = kp_matched_well_len

            print(match_cnt1, match_cnt2)
            print('iter: '+str(count)+', len: '+str(kp_matched_well_len))
        
            if (match_cnt1 <= cnt_th) and (match_cnt2 <= cnt_th):
                print("saving image")
                cv2.imwrite(os.path.join(abs_folder_name, folder_name+'_'+str(image_count)+'.jpg'), frame2)
                image_count += 1
                first_frame = second_frame
                match_cnt1 = 100
                match_cnt2 = 100

        vidcap.release()