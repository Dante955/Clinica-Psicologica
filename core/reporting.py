from sqlalchemy import func
from database.database_manager import session_scope
from database.models import Appointment, Expense, User, UserRole, Income
from datetime import datetime

class ReportingService:

    def get_financial_summary(self, start_date: datetime, end_date: datetime):
        """
        Calcula los ingresos, gastos y beneficios en un rango de fechas.
        """
        with session_scope() as session:
            # Calcular ingresos por citas (completadas y pagadas)
            income_from_appointments = session.query(func.sum(Appointment.price)).filter(
                Appointment.appointment_time.between(start_date, end_date),
                Appointment.status == 'completed',
                Appointment.payment_status == 'pagado'
            ).scalar() or 0.0

            # Calcular otros ingresos desde la nueva tabla Income
            other_income = session.query(func.sum(Income.amount)).filter(
                Income.income_date.between(start_date, end_date)
            ).scalar() or 0.0

            # Calcular gastos totales
            total_expenses = session.query(func.sum(Expense.amount)).filter(
                Expense.expense_date.between(start_date, end_date)
            ).scalar() or 0.0

            total_income = income_from_appointments + other_income
            profit = total_income - total_expenses

            return {
                "income": total_income,
                "expenses": total_expenses,
                "profit": profit
            }

    def get_appointments_per_psychologist(self, start_date: datetime, end_date: datetime):
        """
        Devuelve un diccionario con el número de citas por psicólogo.
        """
        with session_scope() as session:
            # Contar citas por psicólogo
            results = session.query(
                User.username, 
                func.count(Appointment.id)
            ).join(Appointment, User.id == Appointment.psychologist_id).filter(
                User.role == UserRole.PSICOLOGO.value,  # Comparar con el valor string
                Appointment.appointment_time.between(start_date, end_date)
            ).group_by(User.username).all()

            # Convertir el resultado en un diccionario {psicologo: cantidad}
            return {username: count for username, count in results}
