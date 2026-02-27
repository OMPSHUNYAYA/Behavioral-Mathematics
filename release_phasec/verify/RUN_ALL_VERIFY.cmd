@echo off
setlocal

cd /d "%~dp0.."

echo =========================================
echo SBM VERIFY CAPSULE - RUN ALL VERIFY
echo =========================================

python verify\verify_sbm.py --outputs outputs --use_registry --report verify\last_verify_report.txt
set CODE=%ERRORLEVEL%

echo =========================================
if "%CODE%"=="0" (
  echo OVERALL_STATUS: PASS
) else (
  echo OVERALL_STATUS: FAIL
)
echo EXIT_CODE: %CODE%
echo =========================================

exit /b %CODE%