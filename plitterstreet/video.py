"""
    Extracts the images from video based on time interval or gps distance or overlapping based feature matching and also multiple conditions together.
    Usually some of the cameras capture exif information (ex: GoPro cameras) and its recommneded to extract those information in supported tools by camera brand type or ffmpeg tool.
    This class required video in MP4 or AVI format and GPS information in csv or json format.
    The every item or row in the file must contain values in the columns or keys of 'cts', 'date', 'GPS (Lat.) [deg]', 'GPS (Long.) [deg]', 'GPS (Alt.) [m]'
"""

import os, sys
import cv2
import csv
import fractions
from PIL import Image
from PIL.ExifTags import TAGS
from tag_exif import set_gps_location
import geopy.distance

class Video:
    def __init__(self, video_file, gps_file=''):
        if not os.path.isfile(video_file):
            return("File not found", video_file)
        self.vidcap = cv2.VideoCapture(video_file)
        success,image = self.vidcap.read()
        if not success:
            print("Can not read frames in the video!")
        else:
            print("Video is set and ready to make frames")
            self.video_dir = os.path.dirname(video_file)
            self.file_name = os.path.basename(video_file)
        self.vidcap.release()

        self.gps_list = list()
        if not gps_file == '' and os.path.isfile(gps_file):
            if gps_file.endswith('.csv'):
                with open(gps_file, 'r') as csvfile:
                    reader = csv.DictReader(csvfile)
                    for row in reader:
                        self.gps_list.append(
                            [
                                row['cts'], 
                                row['date'], 
                                row['GPS (Lat.) [deg]'], 
                                row['GPS (Long.) [deg]'], 
                                row['GPS (Alt.) [m]']
                            ]
                        )
                    if not len(self.gps_list) == 0:
                        print("GPS poingts found:", len(self.gps_list))
                        self.gps_file = gps_file
                    else:
                        self.gps_file = ''
                        self.gps_list = list()
        else:
            print("Continuing withput GPS file, add it if available.")
            self.gps_file = ''
            self.gps_list = list()

    def ExtractByInterval(self, interval=1, dst_path=''):
        """
            only use if the gps is not available and just want to make frame for evey 'x' seconds from the video.
            dst_path is needed to save the images in that directory, other wise a folder will created with name of video file.
        """
        vidcap = cv2.VideoCapture(os.path.join(self.video_dir, self.file_name))
        success,image = vidcap.read()
        if success:
            if dst_path=='':
                print("destination path is not given, stores the iamges into a created folder with video file name in the directroy to input video")
                dst_path = self.video_dir
            else:
                dst_path = os.path.abspath(dst_path)
            folder_name = os.path.splitext(self.file_name)[0]
            abs_folder_name = os.path.join(dst_path, folder_name)
            try:
                if not os.path.exists(abs_folder_name):
                    os.mkdir(abs_folder_name) 
            except OSError as error: 
                print(error)

        count = 0
        while success:
            vidcap.set(cv2.CAP_PROP_POS_MSEC,(count*interval*1000))
            success,image = vidcap.read()
            if success:
                cv2.imwrite(os.path.join(abs_folder_name, folder_name+'_'+str(count)+'.jpg'), image)
                count += 1
        vidcap.release()
        print("Total " + str(count) + " images are extracted from " + str(self.file_name))

    # To Do
    # def byTimestamp():
        # listTimestamp = []

    def ExtractByOnlyOverlap(self, cnt_th=1, qlt_th=0.7, dst_path=''):
        """
            only use if the gps is not available and just want to save the frame after identifying overlap less than a given threshold, to last frame saved in the video.
            dst_path is needed to save the images in that directory, other wise a folder will created with name of video file.
        """
        vidcap = cv2.VideoCapture(os.path.join(self.video_dir, self.file_name))
        # vidcap.set(cv2.CAP_PROP_POS_MSEC,(20000))
        success, frame1 = vidcap.read()
        if success:
            if dst_path=='':
                print("destination path is not given, stores the iamges into a created folder with video file name in the directroy to input video")
                dst_path = self.video_dir
            else:
                dst_path = os.path.abspath(dst_path)
            folder_name = os.path.splitext(self.file_name)[0]
            abs_folder_name = os.path.join(dst_path, folder_name)
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
        while(success):
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
                print("saving image at frame", count)
                cv2.imwrite(os.path.join(abs_folder_name, folder_name+'_'+str(image_count)+'.jpg'), frame2)
                image_count += 1
                first_frame = second_frame
                match_cnt1 = 100
                match_cnt2 = 100

        vidcap.release()
        print("Total " + str(image_count) + " images are extracted from " + str(self.file_name))
    
    def ExtractbyGps(self, dst_path='', check_overlapping = True, gps_distance=0, cnt_th=1, qlt_th=0.7, skip=0):
        """
            uses gps_pingts in gps_list to save frames, check_overlapping is set to True in default, change to False to avoid.
            gps_ditance is set to 0 in default, provide it with some number (consider in meters) to keep the distnce between images.
        """        
        if len(self.gps_list) < 3:
            return 'Not enough gps data, check the given gps_file.'

        vidcap = cv2.VideoCapture(os.path.join(self.video_dir, self.file_name))
        srat_ts = float(self.gps_list[1][0])
        vidcap.set(cv2.CAP_PROP_POS_MSEC,(srat_ts))
        success, frame1 = vidcap.read()

        if success:
            if dst_path=='':
                print("destination path is not given, stores the iamges into a created folder with video file name in the directroy to input video")
                dst_path = self.video_dir
            else:
                dst_path = os.path.abspath(dst_path)
            folder_name = os.path.splitext(self.file_name)[0]
            abs_folder_name = os.path.join(dst_path, folder_name)
            try:
                if not os.path.exists(abs_folder_name):
                    os.mkdir(abs_folder_name) 
            except OSError as error: 
                print(error)
                
            gps_tag_filename = os.path.join(abs_folder_name, folder_name+'.csv') 
            with open(gps_tag_filename, 'w', newline='') as gps_tag_file:
                gps_tag_writer = csv.DictWriter(gps_tag_file, fieldnames = ['Name', 'Latitude', 'Longitude'], delimiter=',')
                gps_tag_writer.writeheader()
                pivot_frame = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
                count = 0
                image_count = 0
                image_name = os.path.join(abs_folder_name, folder_name+'_'+str(image_count)+'.jpg') 
                cv2.imwrite(image_name, frame1)
                print(float(self.gps_list[1][2]), float(self.gps_list[1][3]), float(self.gps_list[1][4]))
                set_gps_location(image_name, str(self.gps_list[1][1]), float(self.gps_list[1][2]), float(self.gps_list[1][3]), int(float(self.gps_list[1][4])))
                pivot_gps_tag_row = {"Name": folder_name+'_'+str(image_count)+'.jpg', "Latitude": self.gps_list[1][2], "Longitude": self.gps_list[1][3]}
                gps_tag_writer.writerow(pivot_gps_tag_row)
                image_count += 1
                match_cnt1 = 100
                match_cnt2 = 100
                for row in self.gps_list[2:]:
                    if count % (skip+1) != 0:
                        # print("skipping near")
                        count += 1
                        continue
                    distance = geopy.distance.distance((pivot_gps_tag_row['Latitude'], pivot_gps_tag_row['Longitude']), (float(row[2]), float(row[3]))).m
                    print(distance)
                    if distance < (gps_distance - gps_distance*0.15):
                        print('avoiding, gps distance:', distance)
                        count += 1
                        continue
                    # elif distance < (gps_distance - gps_distance*0.15):
                    pts = float(row[0])
                    vidcap.set(cv2.CAP_PROP_POS_MSEC,(pts))
                    success, frame2 = vidcap.read()
                    count += 1
                    if success == False:
                        print('Unable to read frame at', pts)
                        continue
                    next_frame = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)

                    orb = cv2.ORB_create()
                    kp1, kp_des1 = orb.detectAndCompute(pivot_frame, None)
                    kp2, kp_des2 = orb.detectAndCompute(next_frame, None)
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
                        set_gps_location(image_name, row[1], float(row[2]), float(row[3]), float(row[4]))
                        gps_tag_row = {"Name": folder_name+'_'+str(image_count)+'.jpg', "Latitude": row[2], "Longitude": row[3]}
                        gps_tag_writer.writerow(gps_tag_row)
                        pivot_gps_tag_row = gps_tag_row
                        image_count += 1
                        pivot_frame = next_frame
                        match_cnt1 = 100
                        match_cnt2 = 100

                vidcap.release()
            return abs_folder_name