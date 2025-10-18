from flask_restful import Resource, reqparse
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask import jsonify
from models import db, Report, User, Match
from datetime import datetime

class ReportsAPI(Resource):
    @jwt_required()
    def get(self):
        """Get paginated reports with filters"""
        parser = reqparse.RequestParser()
        parser.add_argument('page', type=int, default=1)
        parser.add_argument('per_page', type=int, default=20)
        parser.add_argument('type', choices=['lost', 'found'])
        parser.add_argument('category_id', type=int)
        parser.add_argument('location_id', type=int)
        parser.add_argument('search', type=str)
        args = parser.parse_args()
        
        query = Report.query
        
        if args['type']:
            query = query.filter(Report.type == args['type'])
        if args['category_id']:
            query = query.filter(Report.category_id == args['category_id'])
        if args['search']:
            query = query.filter(Report.item_name.contains(args['search']))
            
        reports = query.paginate(
            page=args['page'], 
            per_page=args['per_page'],
            error_out=False
        )
        
        return {
            'reports': [self._serialize_report(r) for r in reports.items],
            'total': reports.total,
            'pages': reports.pages,
            'current_page': reports.page
        }
    
    @jwt_required()
    def post(self):
        """Create new report"""
        parser = reqparse.RequestParser()
        parser.add_argument('item_name', required=True)
        parser.add_argument('description', required=True)
        parser.add_argument('type', required=True, choices=['lost', 'found'])
        parser.add_argument('category_id', type=int)
        parser.add_argument('location_id', type=int)
        parser.add_argument('reward_amount', type=float, default=0.0)
        args = parser.parse_args()
        
        user_id = get_jwt_identity()
        
        report = Report(
            user_id=user_id,
            item_name=args['item_name'],
            description=args['description'],
            type=args['type'],
            category_id=args['category_id'],
            location_id=args['location_id'],
            reward_amount=args['reward_amount']
        )
        
        db.session.add(report)
        db.session.commit()
        
        return self._serialize_report(report), 201
    
    def _serialize_report(self, report):
        return {
            'id': report.id,
            'item_name': report.item_name,
            'description': report.description,
            'type': report.type,
            'status': report.status,
            'reward_amount': report.reward_amount,
            'created_at': report.created_at.isoformat(),
            'user': {
                'id': report.user.id,
                'username': report.user.username
            }
        }

class MatchingAPI(Resource):
    @jwt_required()
    def post(self):
        """Find matches for a specific report"""
        parser = reqparse.RequestParser()
        parser.add_argument('report_id', type=int, required=True)
        parser.add_argument('threshold', type=float, default=0.5)
        args = parser.parse_args()
        
        # Trigger async matching task
        from tasks import find_matches_task
        task = find_matches_task.delay(args['report_id'], args['threshold'])
        
        return {'task_id': task.id, 'status': 'processing'}, 202

class AnalyticsAPI(Resource):
    @jwt_required()
    def get(self):
        """Get platform analytics"""
        total_reports = Report.query.count()
        lost_reports = Report.query.filter(Report.type == 'lost').count()
        found_reports = Report.query.filter(Report.type == 'found').count()
        resolved_reports = Report.query.filter(Report.status == 'resolved').count()
        
        return {
            'total_reports': total_reports,
            'lost_reports': lost_reports,
            'found_reports': found_reports,
            'resolved_reports': resolved_reports,
            'success_rate': (resolved_reports / total_reports * 100) if total_reports > 0 else 0
        }