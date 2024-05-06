from flask import Flask, render_template, request, redirect, url_for
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.base import JobLookupError
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
import os
from selenium_stealth import stealth
from selenium.webdriver.chrome.service import Service
import imageio.v2 as imageio

app = Flask(__name__)

scheduler = BackgroundScheduler()
scheduler.start()

import os

def latestImage(task_id):
    # List all files in the directory
    files = os.listdir(task_id)
    
    # Filter PNG files
    png_files = [file for file in files if file.lower().endswith('.png')]
    
    if not png_files:
        print("No PNG files found in the directory.")
        return None
    
    # Get file paths with full directory path
    png_files = [os.path.join(task_id, file) for file in png_files]
    
    # Sort files based on modification time
    newest_png = max(png_files, key=os.path.getmtime)
    
    return newest_png


def trackSystem(task_id, systemURL):
    service = Service(executable_path='./chromedriver.exe')
    options = webdriver.ChromeOptions()
    options.add_argument("start-maximized")
    options.add_argument("--headless")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    driver = webdriver.Chrome(
        options=options, service=service)

    stealth(driver,
            languages=["en-US", "en"],
            vendor="Google Inc.",
            platform="Win32",
            webgl_vendor="Intel Inc.",
            renderer="Intel Iris OpenGL Engine",
            fix_hairline=True,
            )


    url = systemURL  # change the url

    driver.get(url)

    driver.set_window_size(1920, 1080)

    time.sleep(10)

    if os.path.exists(f"./static/systems/{task_id}"):
        print("system exists")
    else:
        os.makedirs(f"./static/systems/{task_id}")
        os.makedirs(f"./static/systems/{task_id}/gifs")

    curTime = time.time()
    driver.save_screenshot(f"./static/systems/{task_id}/{curTime}.png")  # change image name   

@app.route('/')
def index():
    # Get list of scheduled job IDs
    scheduled_jobs = [job.id for job in scheduler.get_jobs()]
    latest_images = []
    for folder in os.listdir("./static/systems"):
        folder_path = os.path.join("./static/systems", folder)
        if os.path.isdir(folder_path) and folder != 'gifs':
            latest_image_path = latestImage(folder_path)
            if latest_image_path:
                task = latest_image_path.split("\\")[1]
                if task in scheduled_jobs:
                    latest_images.append(latest_image_path)

    info = []
    for x in range(len(scheduled_jobs)):
        newSystem = [scheduled_jobs[x], latest_images[x]]
        info.append(newSystem)

    return render_template('index.html', info=info)

@app.route('/makegif', methods=['GET'])
def makegif():
    system = request.args.get('system')
    gifDir = f"./static/systems/{system}"
    outDir = f"./static/systems/{system}/gifs/1.gif"
    images = [f for f in os.listdir(gifDir) if f.endswith('.jpg') or f.endswith('.png')]
    images.sort()
    frames = []
    for image_name in images:
        image_path = os.path.join(gifDir, image_name)
        frames.append(imageio.imread(image_path))    
    imageio.mimsave(outDir, frames, 'GIF', duration=len(frames)*.5)

    return render_template('gif.html', gif=outDir)

@app.route('/schedule_task', methods=['POST'])
def schedule_task():
    task_id = request.form['task_id']
    interval = int(request.form['interval'])
    taskURL = request.form['url']
    
    trackSystem(task_id, taskURL)

    scheduler.add_job(trackSystem, 'interval', minutes=interval, id=task_id, args=[task_id, taskURL])
    
    return redirect(url_for('index'))

@app.route('/cancel_task', methods=['POST'])
def cancel_task():
    task_id = request.form['task_id']
    
    try:
        scheduler.remove_job(task_id)
    except JobLookupError:
        pass
    
    return redirect(url_for('index'))

if __name__ == '__main__':
    if os.path.exists("./static") == False:
        os.makedirs("./static")
        os.makedirs("./static/systems")
    app.run(host='0.0.0.0', port=5000)
