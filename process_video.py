#!/usr/bin/env python3
"""
CLI Utility to process individual or batch candidate video clips, analyze frames for rule violations,
calculate violation time intervals, check limits, and organize extracted evidence by Serial Student ID.
"""

import os
import sys
import argparse
import glob
from app.db.session import SessionLocal, engine, Base
from app.ai.video_processor import VideoProcessor

# Ensure database tables exist
Base.metadata.create_all(bind=engine)

def process_single_video(input_path, student_id, student_name, exam_id, sample_fps, limits, output_dir=None):
    db_session = SessionLocal()
    try:
        report = VideoProcessor.process_video_file(
            video_path=input_path,
            output_dir=output_dir,
            sample_fps=sample_fps,
            custom_limits=limits,
            student_id=student_id,
            student_name=student_name,
            exam_id=exam_id,
            db_session=db_session
        )
        return report
    finally:
        db_session.close()

def main():
    parser = argparse.ArgumentParser(
        description="Process candidate video files, check compliance rules, track violation durations, and index by Serial Student ID."
    )
    parser.add_argument(
        "--input", "-i",
        help="Path to input video file (e.g. video.mp4, video.webm)"
    )
    parser.add_argument(
        "--dir", "-d",
        help="Path to directory containing candidate video files for batch processing"
    )
    parser.add_argument(
        "--student-id",
        help="Student ID or Candidate Identifier (default: auto-generates serial STU-001, STU-002, ...)"
    )
    parser.add_argument(
        "--student-name",
        help="Candidate / Student full name"
    )
    parser.add_argument(
        "--exam-id",
        default="MIDTERM-2026",
        help="Exam / Test Identifier (default: MIDTERM-2026)"
    )
    parser.add_argument(
        "--output", "-o",
        help="Output directory (default: ./evidence/candidates/<student_id>/)"
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

    args = parser.parse_args()

    if not args.input and not args.dir:
        print("❌ Error: Must specify either --input <video.mp4> or --dir <folder_path>")
        sys.exit(1)

    custom_limits = {
        "PHONE_DETECTED": args.max_phone,
        "NO_PERSON_DETECTED": args.max_missing
    }

    print(f"\n=======================================================")
    print(f"   CANDIDATE MULTI-ENTRY VIDEO COMPLIANCE PROCESSOR    ")
    print(f"=======================================================")

    if args.input:
        report = process_single_video(
            input_path=args.input,
            student_id=args.student_id,
            student_name=args.student_name,
            exam_id=args.exam_id,
            sample_fps=args.sample_fps,
            limits=custom_limits,
            output_dir=args.output
        )

        print(f"Student ID       : {report['candidate_info']['student_id']}")
        print(f"Student Name     : {report['candidate_info']['student_name']}")
        print(f"Exam ID          : {report['candidate_info']['exam_id']}")
        print(f"Input Video      : {args.input}")
        print(f"Overall Status   : {report['overall_status']}")
        print(f"Limit Exceeded   : {report['overall_limit_exceeded']}")
        print(f"Report JSON Path : {report['report_file_path']}\n")

    elif args.dir:
        video_files = []
        for ext in ("*.mp4", "*.webm", "*.avi", "*.mov"):
            video_files.extend(glob.glob(os.path.join(args.dir, ext)))

        print(f"Batch Processing Directory : {args.dir}")
        print(f"Total Video Files Found    : {len(video_files)}")
        print(f"=======================================================\n")

        for idx, v_path in enumerate(video_files, start=1):
            filename = os.path.basename(v_path)
            s_id = args.student_id

            r = process_single_video(
                input_path=v_path,
                student_id=s_id,
                student_name=args.student_name,
                exam_id=args.exam_id,
                sample_fps=args.sample_fps,
                limits=custom_limits
            )
            print(f"[{idx}] Student '{r['candidate_info']['student_id']}' | File: {filename}")
            print(f"    └── Status: {r['overall_status']} | Duration: {r['video_metadata']['duration_seconds']}s")

        print("\n================ BATCH PROCESSING COMPLETE ================\n")

if __name__ == "__main__":
    main()
