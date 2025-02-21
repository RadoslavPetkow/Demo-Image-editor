PyQt Image Editor

Overview

The PyQt Image Editor is a demo application built using PyQt5 and Python. It showcases a modular approach to image editing by integrating a wide range of features including basic file operations, cropping, resizing, rotation, flipping, color adjustments, filters, freehand drawing with adjustable brush color and size, undo/redo functionality, zooming/panning, and histogram analysis. This project serves as a starting point for further development of more complex image editing tools.

Features
	•	Open and Save Images:
Load images from and save images to various formats (PNG, JPG, JPEG, BMP, GIF).
	•	Cropping Tool:
Select a rectangular area on the image to crop.
	•	Resizing and Scaling:
Dynamically resize images to specified dimensions.
	•	Advanced Rotation:
Rotate images by an arbitrary angle (not just fixed 90° increments).
	•	Flip/Mirror Functions:
Flip images horizontally or vertically.
	•	Color Adjustments:
Adjust brightness, contrast, and saturation using slider controls.
	•	Image Filters and Effects:
Apply filters such as Grayscale, Sepia, Blur, Sharpen, and Edge Detection.
	•	Drawing and Annotation Tools:
Freehand drawing on images with options to choose the brush color and adjust the brush size.
	•	Undo/Redo Functionality:
Maintain a history of editing actions so users can easily undo or redo changes.
	•	Zoom and Pan:
Zoom in and out of the image and pan across large images.
	•	Histogram and Color Analysis:
Display the image’s color histogram for red, green, and blue channels.
	•	Layer Support (Stub):
A placeholder for future implementation of layer support.

Requirements
	•	Python 3.x
	•	PyQt5
	•	Pillow
	•	matplotlib

Installation
	1.	Clone or Download the Repository:
Save the image_editor.py file to your local machine.
	2.	Install Dependencies:
Open your terminal or command prompt and run:

pip install PyQt5 Pillow matplotlib



Running the Application

To run the image editor demo, execute the following command in the directory where image_editor.py is located:

python image_editor.py

Packaging as a Standalone Application

You can package this application into a standalone executable using PyInstaller:
	1.	Install PyInstaller:

pip install pyinstaller
	2.	Create the Executable:
Navigate to the directory containing image_editor.py and run:

pyinstaller --onefile --windowed image_editor.py
	•	The --onefile flag bundles the app into a single executable.
	•	The --windowed flag prevents a terminal window from appearing when the app is run.
	3.	Locate Your Executable:
After the process completes, check the dist folder for your standalone application:
	•	On Windows: You will find image_editor.exe.
	•	On macOS/Linux: The executable will be available and can be further customized into an app bundle if desired.

Usage Instructions
	•	File Operations:
Use the toolbar buttons to open and save images.
	•	Editing Tools:
	•	Click Crop to select and crop a portion of the image.
	•	Use Resize to change image dimensions.
	•	Select Rotate… to rotate the image by a custom angle.
	•	Flip H/V to flip the image horizontally or vertically.
	•	Use Adjust Colors to modify brightness, contrast, and saturation.
	•	Filters:
Click the Filters button to choose from Grayscale, Sepia, Blur, Sharpen, or Edge Detection filters.
	•	Drawing and Annotations:
Toggle Draw mode to start freehand drawing.
	•	Use Brush Color to choose a custom drawing color.
	•	Use Brush Size to adjust the thickness of the drawing brush.
	•	Undo/Redo:
Revert changes using the Undo and Redo buttons.
	•	Zoom and Pan:
Use Zoom In and Zoom Out to adjust the view.
	•	Histogram:
Click Histogram to display the color histogram of the current image.
	•	Layers:
A placeholder for future layer support functionality.

Future Enhancements
	•	Comprehensive layer management.
	•	Enhanced error handling and user interface improvements.
	•	Additional image processing and editing tools.
