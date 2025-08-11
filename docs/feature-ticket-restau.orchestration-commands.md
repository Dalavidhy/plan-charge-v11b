# 🎫 Restaurant Ticket Feature - Orchestration Commands

**Orchestration ID**: TR-ORCH-001  
**Status**: READY TO EXECUTE  
**Created**: 2025-01-25  

## 🚀 Quick Start

### 1. Start Orchestration
```bash
# Start with interactive confirmation
./scripts/orchestration-launcher.sh start

# Or use the Python controller directly
python3 scripts/orchestration-controller.py start --config docs/feature-ticket-restau.orchestration-config.yaml
```

### 2. Monitor Progress
```bash
# Open monitoring dashboard (auto-starts with launcher)
python3 scripts/orchestration-monitor.py

# Check status
./scripts/orchestration-launcher.sh status
```

### 3. View Logs
```bash
# Show recent logs
./scripts/orchestration-launcher.sh logs

# Tail controller logs
tail -f logs/orchestration/controller.log

# Tail monitor logs
tail -f logs/orchestration/monitor.log
```

## 🎮 Control Commands

### Stream Management
```bash
# Pause a specific stream
python3 scripts/orchestration-controller.py pause --stream stream-b-frontend

# Resume a paused stream
python3 scripts/orchestration-controller.py resume --stream stream-b-frontend

# Emergency stop all streams
./scripts/orchestration-launcher.sh stop
```

### Agent Management
```bash
# Reallocate agent to different stream
python3 scripts/orchestration-controller.py reallocate --agent agent-c1 --to-stream stream-a-backend

# Check agent health
python3 scripts/orchestration-controller.py health --agent agent-a1
```

### Checkpoint Validation
```bash
# Force checkpoint validation
python3 scripts/orchestration-controller.py validate --checkpoint cp-1 --force

# Skip checkpoint (requires override permission)
python3 scripts/orchestration-controller.py skip --checkpoint cp-2 --reason "Manual validation completed"
```

## 📊 Monitoring Commands

### Dashboard Views
```bash
# Full dashboard (default)
python3 scripts/orchestration-monitor.py

# Stream-specific view
python3 scripts/orchestration-monitor.py --stream stream-a-backend

# Agent performance view
python3 scripts/orchestration-monitor.py --view agents

# Task progress view
python3 scripts/orchestration-monitor.py --view tasks
```

### Metrics Export
```bash
# Export current metrics
python3 scripts/orchestration-controller.py export --format json > metrics.json

# Generate progress report
python3 scripts/orchestration-controller.py report --output progress-report.html
```

## 🚨 Emergency Commands

### Critical Situations
```bash
# Emergency stop (saves state)
python3 scripts/orchestration-controller.py stop --emergency --reason "Critical bug found"

# Rollback to checkpoint
python3 scripts/orchestration-controller.py rollback --to-checkpoint cp-2

# Dump current state
python3 scripts/orchestration-controller.py dump-state --output state-backup.json
```

### Recovery
```bash
# Resume from saved state
python3 scripts/orchestration-controller.py resume --from-state state-backup.json

# Restart failed tasks
python3 scripts/orchestration-controller.py retry --failed-tasks

# Reset stream
python3 scripts/orchestration-controller.py reset --stream stream-c-testing
```

## 🔧 Configuration Commands

### Update Configuration
```bash
# Reload configuration (hot reload)
python3 scripts/orchestration-controller.py reload-config

# Validate configuration
python3 scripts/orchestration-controller.py validate-config --config new-config.yaml

# Apply configuration patch
python3 scripts/orchestration-controller.py patch --file config-updates.yaml
```

### Performance Tuning
```bash
# Adjust parallelism
python3 scripts/orchestration-controller.py tune --max-parallel 4

# Change monitoring interval
python3 scripts/orchestration-controller.py tune --monitor-interval 10

# Enable/disable safety mode
python3 scripts/orchestration-controller.py safety --mode strict
```

## 📋 Task Management

### Task Operations
```bash
# Add new task
python3 scripts/orchestration-controller.py add-task --file new-task.yaml

# Update task priority
python3 scripts/orchestration-controller.py update-task --id A1.1 --priority critical

# Block/unblock task
python3 scripts/orchestration-controller.py block-task --id B2.1 --reason "Waiting for design approval"
python3 scripts/orchestration-controller.py unblock-task --id B2.1
```

### Dependency Management
```bash
# Add dependency
python3 scripts/orchestration-controller.py add-dep --task B3.1 --depends-on A3.2

# Remove dependency
python3 scripts/orchestration-controller.py remove-dep --task B3.1 --dependency A3.2

# Visualize dependencies
python3 scripts/orchestration-controller.py viz-deps --output dependencies.png
```

## 🔍 Debugging Commands

### Troubleshooting
```bash
# Enable debug logging
python3 scripts/orchestration-controller.py debug --enable

# Trace task execution
python3 scripts/orchestration-controller.py trace --task A2.1

# Analyze bottlenecks
python3 scripts/orchestration-controller.py analyze --bottlenecks
```

### Performance Analysis
```bash
# Profile execution
python3 scripts/orchestration-controller.py profile --duration 300

# Memory usage
python3 scripts/orchestration-controller.py memory --agents

# Network latency
python3 scripts/orchestration-controller.py latency --check
```

## 🎯 Example Workflows

### Daily Operations
```bash
# Morning startup
./scripts/orchestration-launcher.sh start
python3 scripts/orchestration-controller.py status

# Midday check
python3 scripts/orchestration-controller.py progress
python3 scripts/orchestration-controller.py health --all

# End of day
python3 scripts/orchestration-controller.py report --daily
./scripts/orchestration-launcher.sh stop
```

### Handling Issues
```bash
# Task failure
python3 scripts/orchestration-controller.py investigate --task A2.1
python3 scripts/orchestration-controller.py retry --task A2.1

# Stream delay
python3 scripts/orchestration-controller.py analyze --stream stream-b-frontend
python3 scripts/orchestration-controller.py reallocate --from stream-c-testing --to stream-b-frontend

# Checkpoint failure
python3 scripts/orchestration-controller.py checkpoint-status --id cp-2
python3 scripts/orchestration-controller.py validate --checkpoint cp-2 --manual
```

## 📈 Reporting Commands

### Generate Reports
```bash
# Daily progress report
python3 scripts/orchestration-controller.py report --type daily --format pdf

# Stream performance report
python3 scripts/orchestration-controller.py report --type stream --stream stream-a-backend

# Agent utilization report
python3 scripts/orchestration-controller.py report --type utilization --format csv

# Risk assessment report
python3 scripts/orchestration-controller.py report --type risk --include-mitigation
```

## 🔒 Safety Protocols

### Enable Safety Features
```bash
# Strict safety mode (all checkpoints blocking)
python3 scripts/orchestration-controller.py safety --mode strict

# Balanced safety mode (critical checkpoints only)
python3 scripts/orchestration-controller.py safety --mode balanced

# Relaxed safety mode (warnings only)
python3 scripts/orchestration-controller.py safety --mode relaxed
```

### Audit Commands
```bash
# Generate audit trail
python3 scripts/orchestration-controller.py audit --from "2025-01-27" --to "2025-02-07"

# Compliance check
python3 scripts/orchestration-controller.py compliance --standards "ISO-9001,GDPR"

# Security scan
python3 scripts/orchestration-controller.py security-scan --deep
```

## 💡 Tips & Best Practices

1. **Always start with status check**: `./scripts/orchestration-launcher.sh status`
2. **Monitor critical paths**: Focus on Stream A (backend) as it blocks others
3. **Use checkpoints**: Don't skip unless absolutely necessary
4. **Keep logs**: All operations are logged in `logs/orchestration/`
5. **Regular backups**: Use `dump-state` command daily
6. **Test in dry-run**: Add `--dry-run` to any command to simulate

## 🆘 Support

- **Documentation**: See `docs/feature-ticket-restau.*.md` files
- **Logs**: Check `logs/orchestration/` directory
- **Config**: Edit `docs/feature-ticket-restau.orchestration-config.yaml`
- **Issues**: Create tickets with orchestration ID TR-ORCH-001

---

**Note**: All commands support `--help` flag for detailed usage information.