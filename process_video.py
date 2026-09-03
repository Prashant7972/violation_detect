#!/usr/bin/env python3
"""
CLI Utility to process an input video clip, analyze frames for rule violations,
calculate violation time intervals, check limits, and extract evidence snapshots.
"""

import sys
import argparse
import json
from app.ai.video_processor import VideoProcessor

def main():
    parser = argparse.ArgumentParser(
        description="Process a video file, check compliance rules, track violation durations, and extract evidence."
    )
    parser.add_argument(
        "--input", "-i",
        required=True,
        help="Path to input video file (e.g. video.mp4, video.webm)"
    )
    parser.add_argument(
        "--output", "-o",
        default="./output_analysis",
        help="Output directory to save report and extracted evidence keyframes (default: ./output_analysis)"
    )
    parser.add_argument(
        "--sample-fps", "-s",
        type=float,
        default=1.0,
        help="Sampling rate in frames per second (default: 1.0)"
    )
    parser.add_argument(
        "--max-phone",
        type=float,
        default=5.0,
        help="Maximum allowed phone usage limit in seconds (default: 5.0)"
    )
    parser.add_argument(
        "--max-missing",
        type=float,
        default=10.0,
        help="Maximum allowed candidate missing limit in seconds (default: 10.0)"
    )
    parser.add_argument(
        "--max-multiple",
        type=float,
        default=3.0,
        help="Maximum allowed multiple persons limit in seconds (default: 3.0)"
    )

    args = parser.parse_args()

    custom_limits = {
        "PHONE_DETECTED": args.max_phone,
        "NO_PERSON_DETECTED": args.max_missing,
        "MULTIPLE_PERSONS": args.max_multiple
    }

    print(f"\n=======================================================")
    print(f"       AI VIDEO CLIP COMPLIANCE PROCESSOR              ")
    print(f"=======================================================")
    print(f"Input Video File : {args.input}")
    print(f"Output Directory : {args.output}")
    print(f"Sampling Rate    : {args.sample_fps} FPS")
    print(f"Duration Limits  : {custom_limits}")
    print(f"=======================================================\n")

    try:
        report = VideoProcessor.process_video_file(
            video_path=args.input,
            output_dir=args.output,
            sample_fps=args.sample_fps,
            custom_limits=custom_limits
        )

        print("\n================ ANALYSIS COMPLETE ================")
        print(f"Video Duration   : {report['video_metadata']['duration_formatted']} ({report['video_metadata']['duration_seconds']}s)")
        print(f"Overall Status   : {report['overall_status']}")
        print(f"Limit Exceeded   : {report['overall_limit_exceeded']}")
        print(f"Total Violations : {report['total_violation_intervals_count']} interval(s)")
        print("\n--- Cumulative Violation Durations ---")
        for ev_type, info in report['limit_enforcement'].items():
            status_str = "EXCEEDED ❌" if info['limit_exceeded'] else "OK ✅"
            print(f" - {ev_type:<20}: {info['cumulative_duration_seconds']}s / {info['limit_threshold_seconds']}s [{status_str}]")

        print(f"\nReport Summary saved to : {report['report_file_path']}")
        print("===================================================\n")

    except Exception as e:
        print(f"\n❌ Error processing video file: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
