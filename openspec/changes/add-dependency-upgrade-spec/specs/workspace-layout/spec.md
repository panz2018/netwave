# Spec Delta

## REMOVED Requirements

### Requirement: 版本底线

**Reason**: 版本数字（Rust edition/MSRV、Python/Node 底线、`packageManager`
钉死等）的唯一真相源迁至 `dependency-upgrade` spec 与钉死点登记表
`scripts/version_pins.json`；本 spec 回归目录结构与发布名解耦职责，
避免版本数字双处维护漂移。

**Migration**: 版本底线要求由 `dependency-upgrade` spec 承接——选线原则与
底线取值见其「选线原则——钉 LTS/稳定线」Requirement 与登记表；
`packageManager`/`uv.lock` 等钉死点校验改由 `scripts/check_version_pins.py`
闸门（接进 `check:meta`）执行。原「底线版本可校验」Scenario 的断言目标
不变，只是真相源换家。
