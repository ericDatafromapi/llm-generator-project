#!/bin/bash
# Organize debugging files created during production troubleshooting

echo "=========================================="
echo "📁 Organizing Debug Files"
echo "=========================================="
echo ""

cd /Users/ericbadarou/Documents/personal_projects/website_llm_data

# Move documentation to docs/production_debugging
echo "Moving documentation files to docs/production_debugging..."
mv CELERY_WORKER_FIX.md docs/production_debugging/
mv PRODUCTION_TEST_RESULTS.md docs/production_debugging/
mv PRODUCTION_TESTING_GUIDE.md docs/production_debugging/
mv QUICK_TEST_COMMANDS.md docs/production_debugging/

# Keep PRODUCTION_FIXES.md in root (main reference)
echo "✅ Main documentation organized"

echo ""
echo "Moving one-time debug scripts to scripts/debug_archive..."
mv scripts/check_celery_service.sh scripts/debug_archive/
mv scripts/check_frontend_config.sh scripts/debug_archive/
mv scripts/check_stripe_webhook_config.sh scripts/debug_archive/
mv scripts/check_subscription_step1.sh scripts/debug_archive/
mv scripts/debug_generation.sh scripts/debug_archive/
mv scripts/debug_subscription.sh scripts/debug_archive/
mv scripts/debug_task_flow.sh scripts/debug_archive/
mv scripts/FINAL_FIX.sh scripts/debug_archive/
mv scripts/fix_celery_worker.sh scripts/debug_archive/
mv scripts/fix_queue_issue.sh scripts/debug_archive/
mv scripts/SIMPLE_FIX.sh scripts/debug_archive/
mv scripts/test_frontend_backend_connection.sh scripts/debug_archive/
mv scripts/setup_stripe_webhook.md scripts/debug_archive/

echo "✅ Debug scripts archived"

echo ""
echo "Keeping useful scripts in scripts/:"
echo "  ✅ test_generation_workflow.py - Test generation"
echo "  ✅ test_stripe_subscription.py - Test Stripe"
echo "  ✅ test_production.py - Full production test"
echo "  ✅ install-docker.sh - Docker installation"
echo "  ✅ deploy.sh - Deployment"
echo "  ✅ llmready-celery-worker.service - Service file"
echo "  ✅ setup-celery-services.sh - Service setup"

echo ""
echo "=========================================="
echo "✅ Organization Complete"
echo "=========================================="
echo ""
echo "File structure:"
echo "  Root:"
echo "    - PRODUCTION_FIXES.md (main reference)"
echo "    - README.md"
echo ""
echo "  docs/production_debugging/:"
echo "    - CELERY_WORKER_FIX.md"
echo "    - PRODUCTION_TEST_RESULTS.md"
echo "    - PRODUCTION_TESTING_GUIDE.md"
echo "    - QUICK_TEST_COMMANDS.md"
echo ""
echo "  scripts/:"
echo "    - test_*.py (testing tools - KEEP)"
echo "    - install-docker.sh (KEEP)"
echo "    - deploy.sh (KEEP)"
echo "    - *.service files (KEEP)"
echo ""
echo "  scripts/debug_archive/:"
echo "    - All one-time debug scripts (can delete after deployment)"
echo "=========================================="