'''
converts video to frames and saves images by different interval, or overlap, etc
'''
import os
import cv2
import csv
import sys
import fractions
from PIL import Image
from PIL.ExifTags import TAGS
from .tag_exif import set_gps_location

class Video:
    def __init__(self, file_name, gps_file=''):
        self.file_name = file_name
        self.base_name = os.path.basename(file_name)
        self.vidcap = cv2.VideoCapture(self.file_name) 
        success,image = self.vidcap.read()
        if not success:
            print("Can not read frames in the video!")
        else:
            print("Video is set and ready to make frames")
        self.vidcap.release()

        if not gps_file == '':
            self.gps_file = gps_file
        #     with open(gps_file, 'r') as csvfile:
        #         reader = csv.reader(f)

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

    def byOverlap(self, cnt_th=1, qlt_th=0.7, out_path=''):
        vidcap = cv2.VideoCapture(self.file_name)
        # vidcap.set(cv2.CAP_PROP_POS_MSEC,(20000))
        success, frame1 = vidcap.read()
        if success:
            if out_path=='':
                print("output path not selected, stores the iamges in the basepath to input video")
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
    
    def byGps(self, cnt_th=1, qlt_th=0.7, out_path=''):
        gps_list = []
        if not self.gps_file == '':
            with open(self.gps_file, 'r') as csvfile:
                reader = csv.reader(csvfile)
                for row in reader:
                    gps_list.append(row)
        
        vidcap = cv2.VideoCapture(self.file_name)
        sts = float(gps_list[1][0])
        vidcap.set(cv2.CAP_PROP_POS_MSEC,(sts))
        success, frame1 = vidcap.read()

        if success:
            if out_path=='':
                print("output path not selected, stores the iamges in the basepath to input video")
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
                
            gps_tag_filename = os.path.join(abs_folder_name, folder_name+'.csv') 
            with open(gps_tag_filename, 'w') as gps_tag_file:
                gps_tag_writer = csv.writer(gps_tag_file, delimiter=',')

                first_frame = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
                count = 0
                image_count = 0
                image_name = os.path.join(abs_folder_name, folder_name+'_'+str(image_count)+'.jpg') 
                cv2.imwrite(image_name, frame1)
                print(float(gps_list[1][2]), float(gps_list[1][3]), float(gps_list[1][4]))
                set_gps_location(image_name, str(gps_list[1][1]), float(gps_list[1][2]), float(gps_list[1][3]), int(float(gps_list[1][4])))
                gps_tag_row = [folder_name+'_'+str(image_count)+'.jpg', gps_list[1][2], gps_list[1][3]]
                gps_tag_writer.writerow(gps_tag_row)
                image_count += 1
                match_cnt1 = 100
                match_cnt2 = 100
                for row in gps_list[2:]:
                    pts = float(row[0])
                    vidcap.set(cv2.CAP_PROP_POS_MSEC,(pts))
                    success, frame2 = vidcap.read()
                    count += 1
                    if success == False:
                        print('Unable to read frame at', pts)
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
                        print("saving image at", pts)
                        image_name = os.path.join(abs_folder_name, folder_name+'_'+str(image_count)+'.jpg') 
                        cv2.imwrite(image_name, frame2)
                        set_gps_location(image_name, gps_list[1][1], float(gps_list[1][2]), float(gps_list[1][3]), float(gps_list[1][4]))
                        gps_tag_row = [folder_name+'_'+str(image_count)+'.jpg', row[2], row[3]]
                        gps_tag_writer.writerow(gps_tag_row)
                        image_count += 1
                        first_frame = second_frame
                        match_cnt1 = 100
                        match_cnt2 = 100

                vidcap.release()
        return abs_folder_name



class pLimage():
    def __init__(self):
        self.plimages = []
        self.plidios = []

    def addImages(self, path):
        if type(path) is str:
            if os.path.isfile(path) and path.endswith(('.jpg', '.png', '.tif')):
                self.plimages.append(path)
            elif os.path.isdir(path):
                self.plimages.extend([os.path.join(path, f) for f in os.listdir(path) if f.endswith(('.jpg', '.png', '.tif')) and os.path.isfile(os.path.join(path, f))])
        elif type(path) is list:
            self.plimages.extend([f for f in path if f.endswith(('.jpg', '.png', '.tif')) and os.path.isfile(f)])
        print("Total", len(self.plimages), "images.")

    def addVideoImages(self, video_path, gps_path):
        if (os.path.isfile(video_path) and video_path.endswith(('.mp4', '.avi', '.mkl'))) and (os.path.isfile(gps_path) and gps_path.endswith(('.csv'))):
            video = Video(file_name=video_path, gps_file=gps_path)
            folder_path = video.byGps(cnt_th=1, qlt_th=0.7, out_path='')
            self.addImages(folder_path)