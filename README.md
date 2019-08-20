# Setup

install python 3.6.8 (or 3.6.7 if corrupted)
install libraries if missing (see requirements.txt)
* at least at windows it is required to install libzbar0

for using life stream: 
	connect realsense camera 
	place four QR-codes to set the lego detection board

for using video (.bag) without camera:
	use an optional parameter 'usestream' with the .bag file name
(Note: .bag file can be recorded with RecordVideo/RecordVideo.py using realsense camera)

for saving the output as .avi file:
	def run(self, record_video=True):

# Run

DEPRECATED
run the server
start LegoDetection/LegoDetection.py

# Paramaters
Optional:
--threshold 
  set another then default threshold for black-white image to recognize qr-codes
--usestream USESTREAM
  path and name of the file with saved .bag stream

# Examples
python.exe (...)/LegoDetection/LegoDetection.py
(...)/python.exe (...)/LegoDetection/LegoDetection.py --usestream=stream.bag --threshold=155