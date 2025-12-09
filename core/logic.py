from database.database_manager import session_scope
from database.models import Patient, Appointment, Income
from datetime import datetime

class ClinicLogic:
    """
    Clase que centraliza la lógica de negocio de la aplicación.
    """

    def delete_patient(self, patient_id: int):
        """
        Elimina un paciente y todos sus datos asociados (citas, etc.).
        Devuelve (True, mensaje_exito) o (False, mensaje_error).
        """
        try:
            with session_scope() as session:
                patient_to_delete = session.get(Patient, patient_id)
                if patient_to_delete:
                    patient_name = patient_to_delete.full_name
                    session.delete(patient_to_delete)
                    return True, f"El paciente '{patient_name}' ha sido eliminado correctamente."
                else:
                    return False, "No se encontró el paciente para eliminar."
        except Exception as e:
            return False, f"Ocurrió un error de base de datos al eliminar el paciente:\n{e}"

    def save_appointment(self, patient_id: int, psychologist_id: int, appointment_data: dict, appointment_id: int = None):
        """
        Guarda (crea o actualiza) una cita y maneja la lógica de ingresos.
        appointment_data es un diccionario con los datos de la cita.
        Devuelve (True, mensaje_exito) o (False, mensaje_error).
        """
        try:
            with session_scope() as session:
                patient = session.get(Patient, patient_id)
                if not patient:
                    return False, "Paciente no encontrado."

                appointment = session.get(Appointment, appointment_id) if appointment_id else Appointment(
                    patient_id=patient_id,
                    psychologist_id=psychologist_id
                )
                if not appointment:
                    return False, "Cita no encontrada para editar."

                if not appointment_id:
                    session.add(appointment)

                # Actualizar datos de la cita
                for key, value in appointment_data.items():
                    setattr(appointment, key, value)

                # Lógica de Ingresos
                if appointment.payment_status == "pagada":
                    if not appointment.income:
                        appointment.income = Income()
                    appointment.income.description = f"Pago cita: {patient.full_name} - {appointment.appointment_time.strftime('%d/%m/%Y')}"
                    appointment.income.amount = appointment.price
                    appointment.income.income_date = appointment.appointment_time
                elif appointment.income:
                    session.delete(appointment.income)

            return True, "Cita guardada correctamente."
        except Exception as e:
            return False, f"Ocurrió un error al guardar la cita:\n{e}"