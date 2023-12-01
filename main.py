from PIL import Image
from fastapi import FastAPI, HTTPException, Query
from moviepy.editor import VideoFileClip
import base64
from multiprocessing import Pool

app = FastAPI()

fps = 30

MovieList = {
    "ShrekMovie": "VideoFolder/ShrekMOV.mov",
}

def get_frame_data(frame):
    img = Image.fromarray(frame)
    img = img.resize((160, 90))
    img = img.convert("RGB")
    return img.tobytes().hex()

@app.get('/video/')
async def get_video(
    movie_name: str = Query(..., description="Name of the movie"),
    buffer_length: int = Query(10, description="Buffer length in frames (default: 10)"),
    start_point: int = Query(0, description="Start point in frames (default: 0)"),
):
    print(movie_name, buffer_length, start_point)

    if movie_name not in MovieList:
        raise HTTPException(status_code=404, detail="Movie not found")

    movie_path = MovieList[movie_name]

    clip = VideoFileClip(movie_path)
    
    total_frames = int(clip.fps * clip.duration)
    buffer_length = min(buffer_length, total_frames - start_point)
    end_point = start_point + buffer_length

    tables = []
    bitmap_data_list = []

    with Pool() as pool:
        for i, frame_data in enumerate(pool.imap_unordered(get_frame_data, clip.iter_frames(fps=fps), chunksize=1), start=1):
            if i < start_point:
                continue

            bitmap_data_list.append(frame_data)

            if len(bitmap_data_list) == buffer_length:
                tables.append(bitmap_data_list)
                bitmap_data_list = []
                break

    if bitmap_data_list:
        tables.append(bitmap_data_list)

    tables = [[base64.b64encode(bytes.fromhex(frame_data)).decode('utf-8') for frame_data in table] for table in tables]

    responseData = {
        "map": tables,
        "frame_count": buffer_length
    }

    return responseData

@app.get('/movies/')
def get_movies():
    formattedList = {}
    for movie_name in MovieList:
        img = Image.open("Thumbnails/" + movie_name)
        img = img.resize((720, 480))
        img = img.convert("RGB")
        bitmap_data = img.tobytes().hex()

        formattedList[movie_name] = bitmap_data

    return {'movie_list': formattedList}

@app.get('/frame_count/')
def get_frame_count(movie_name: str = Query(..., description="Name of the movie")):
    # Check if the movie name exists in the MovieList dictionary
    if movie_name not in MovieList:
        raise HTTPException(status_code=404, detail="Movie not found")

    movie_path = MovieList[movie_name]
    clip = VideoFileClip(movie_path)
    frame_count = int(clip.fps * clip.duration)

    return {'frame_count': frame_count}