from celery import Celery
from flask import current_app
import os

def make_celery(app):
    celery = Celery(
        app.import_name,
        backend=app.config['CELERY_RESULT_BACKEND'],
        broker=app.config['CELERY_BROKER_URL']
    )
    celery.conf.update(app.config)
    return celery

celery = Celery('lostfound')

@celery.task
def find_matches_task(report_id, threshold=0.5):
    """Background task for finding matches"""
    from models import Report, Match, db
    from app import simple_image_similarity, calculate_similarity
    
    report = Report.query.get(report_id)
    if not report:
        return {'error': 'Report not found'}
    
    # Find opposite type reports
    opposite_type = 'found' if report.type == 'lost' else 'lost'
    candidates = Report.query.filter(
        Report.type == opposite_type,
        Report.status == 'active'
    ).all()
    
    matches = []
    for candidate in candidates:
        # Calculate similarity
        text_sim = calculate_similarity(
            f"{report.item_name} {report.description}",
            f"{candidate.item_name} {candidate.description}"
        )
        
        if text_sim >= threshold:
            # Check if match already exists
            existing_match = Match.query.filter(
                Match.lost_report_id == (report.id if report.type == 'lost' else candidate.id),
                Match.found_report_id == (candidate.id if report.type == 'lost' else report.id)
            ).first()
            
            if not existing_match:
                match = Match(
                    lost_report_id=report.id if report.type == 'lost' else candidate.id,
                    found_report_id=candidate.id if report.type == 'lost' else report.id,
                    similarity_score=text_sim,
                    text_similarity=text_sim * 100
                )
                db.session.add(match)
                matches.append(match.id)
    
    db.session.commit()
    return {'matches_found': len(matches), 'match_ids': matches}

@celery.task
def send_email_notification(user_id, subject, message):
    """Background task for sending emails"""
    from flask_mail import Message
    from extensions import mail
    from models import User
    
    user = User.query.get(user_id)
    if user:
        msg = Message(
            subject=subject,
            recipients=[user.email],
            body=message
        )
        mail.send(msg)
        return {'status': 'sent', 'email': user.email}
    return {'status': 'error', 'message': 'User not found'}

@celery.task
def cleanup_expired_reports():
    """Background task to cleanup old reports"""
    from models import Report, db
    from datetime import datetime, timedelta
    
    expiry_date = datetime.utcnow() - timedelta(days=90)
    expired_reports = Report.query.filter(
        Report.created_at < expiry_date,
        Report.status == 'active'
    ).all()
    
    for report in expired_reports:
        report.status = 'expired'
    
    db.session.commit()
    return {'expired_count': len(expired_reports)}