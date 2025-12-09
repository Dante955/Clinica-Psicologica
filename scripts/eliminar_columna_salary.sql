-- Script para eliminar la columna salary de la tabla users
-- Ejecutar en SQL Server Management Studio o Azure Data Studio

USE clinic_db;
GO

-- Verificar si la columna existe antes de eliminarla
IF EXISTS (
    SELECT * FROM sys.columns 
    WHERE object_id = OBJECT_ID('dbo.users') 
    AND name = 'salary'
)
BEGIN
    PRINT 'Eliminando columna salary de la tabla users...';
    
    ALTER TABLE dbo.users
    DROP COLUMN salary;
    
    PRINT '✓ Columna salary eliminada exitosamente.';
    PRINT '';
    PRINT 'Los salarios ahora se gestionan exclusivamente como gastos.';
    PRINT 'Usa el tipo de gasto "salario" en el formulario de gastos.';
END
ELSE
BEGIN
    PRINT '✓ La columna salary no existe en la tabla users.';
    PRINT 'No se requiere ninguna acción.';
END
GO

-- Verificar la estructura actual de la tabla users
PRINT '';
PRINT 'Estructura actual de la tabla users:';
PRINT '====================================';
SELECT 
    COLUMN_NAME as 'Columna',
    DATA_TYPE as 'Tipo',
    IS_NULLABLE as 'Nullable'
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME = 'users'
ORDER BY ORDINAL_POSITION;
GO
