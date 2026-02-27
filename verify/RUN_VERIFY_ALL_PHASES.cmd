@echo off
setlocal

echo ========================================
echo SBM MULTI-PHASE VERIFY (A+B+C)
echo ========================================

set AERR=0
set BERR=0
set CERR=0

echo.
echo --- Phase A Replay Check (digitsum_mod9) ---
fc /b "..\reference_outputs\phase_a\OUT_SBM_DIGITS_A_PRIMARY\sbm_manifest.sha256" "..\reference_outputs\phase_a\OUT_SBM_DIGITS_A_REPLAY\sbm_manifest.sha256" >nul
set AERR=%errorlevel%
if not "%AERR%"=="0" (
echo PHASE_A_STATUS: FAIL (manifest mismatch)
) else (
echo PHASE_A_STATUS: PASS
)

echo.
echo --- Phase B Replay Check (xorshift_parity) ---
fc /b "..\reference_outputs\phase_b\anchors\PRIMARY_sbm_manifest.sha256" "..\reference_outputs\phase_b\anchors\REPLAY_sbm_manifest.sha256" >nul
set BERR=%errorlevel%
if not "%BERR%"=="0" (
echo PHASE_B_STATUS: FAIL (manifest mismatch)
) else (
echo PHASE_B_STATUS: PASS
)

echo.
echo --- Phase C Capsule Verify ---
pushd "..\release_phasec\verify" >nul
call RUN_ALL_VERIFY.cmd >nul
set CERR=%errorlevel%
popd >nul
if not "%CERR%"=="0" (
echo PHASE_C_STATUS: FAIL
) else (
echo PHASE_C_STATUS: PASS
)

echo.


set SBM_FAIL=0
if not "%AERR%"=="0" set SBM_FAIL=1
if not "%BERR%"=="0" set SBM_FAIL=1
if not "%CERR%"=="0" set SBM_FAIL=1


if "%SBM_FAIL%"=="0" (
echo OVERALL_STATUS: PASS
echo EXIT_CODE: 0
exit /b 0
) else (
echo OVERALL_STATUS: FAIL
echo EXIT_CODE: 1
exit /b 1
)