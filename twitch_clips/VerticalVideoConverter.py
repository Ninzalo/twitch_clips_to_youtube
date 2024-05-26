from pathlib import Path
from typing import Tuple

from moviepy.editor import ColorClip, CompositeVideoClip, VideoFileClip


class VerticalVideoConverter:
    @staticmethod
    def create_background_file(
        output_file_path: Path,
        duration: int,
        framerate: int,
        size: Tuple[int, int] | None = None,
        color: Tuple[int, int, int] | None = None,
    ) -> Path:
        if color is None:
            color = (0, 0, 0)
        if size is None:
            size = (1080, 1920)
        try:
            ColorClip(
                size=size,
                color=color,
                duration=duration,
            ).write_videofile(
                str(output_file_path),
                fps=framerate,
                logger=None,
            )
            return Path(output_file_path)
        except Exception as e:
            raise RuntimeError("Error creating background file") from e

    @staticmethod
    def create_vertical_video(
        clip_path: Path,
        background_path: Path,
        output_path: Path,
    ) -> Path:
        try:
            clip = VideoFileClip(str(clip_path))
            clip = clip.subclip(0, clip.duration)
            resized_clip = clip.resize(width=1080)
            centered_resized_clip = resized_clip.with_position(
                ("center", "center")
            )
            background = VideoFileClip(str(background_path))
            video = CompositeVideoClip([background, centered_resized_clip])
            video.write_videofile(
                str(output_path),
                audio_codec="aac",
                logger=None,
            )
            return output_path
        except Exception as e:
            raise RuntimeError("Failed to create vertical video") from e
