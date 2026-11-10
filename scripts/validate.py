"""本地结构检查与协议模拟；不连接任何真实 BOT。"""
from pathlib import Path
import hashlib
import re

ROOT = Path(__file__).resolve().parents[1]

class Relay:
    def __init__(self):
        self.round = 1
        self.polling = True
        self.target = {}
        self.receipts = {}
        self.sends = 0

    def send(self, direction, content, disconnect=False):
        key = ('DEMO-001', self.round, direction,
               hashlib.sha256(content.encode()).hexdigest())
        # 恢复时首先查目标端，不能仅看本地回执。
        if key in self.target:
            self.receipts[key] = self.target[key]
            return 'already-received'
        self.sends += 1
        self.target[key] = f'MSG-DEMO-{self.sends}'
        if not disconnect:
            self.receipts[key] = self.target[key]
        return 'sent'

    def review(self, action, next_instruction=None):
        if not self.polling:
            raise ValueError('工作包已完成')
        if action == '继续':
            if not next_instruction:
                raise ValueError('缺少完整下一轮指令')
            self.round += 1
            self.send('to-weasel', next_instruction)
        elif action == '完成':
            self.polling = False
        elif action not in ('待材料', '待用户决定'):
            raise ValueError('非法动作')


def main():
    for path in ROOT.rglob('*.md'):
        for link in re.findall(r'(?<!!)\[[^\]]*\]\(([^)]+)\)', path.read_text()):
            if '://' not in link and not link.startswith('#'):
                assert (path.parent / link.split('#')[0]).exists(), (path, link)
    skill = (ROOT / 'skills/relay-research-review/SKILL.md').read_text()
    assert skill.startswith('---\nname: relay-research-review\ndescription: ')
    assert '\n---\n' in skill[4:]
    template = (ROOT / 'templates/新项目启动模板.md').read_text()
    for field in ('项目名称', '目标对话', 'Codex 工作区', '授权范围'):
        assert field in template
    assert template.count('```text') == 2
    r = Relay()
    r.send('to-review', 'index.md v1')
    instruction = '第2轮完整示例任务书：修改分类，交付v2，核对标题，授权仅编辑索引。'
    r.review('继续', instruction)
    assert r.round == 2 and r.polling
    assert any(k[-1] == hashlib.sha256(instruction.encode()).hexdigest() for k in r.target)
    r.send('to-review', 'index.md v2')
    r.review('完成')
    assert r.round == 2 and not r.polling
    try:
        r.review('继续', instruction)
    except ValueError:
        pass
    else:
        raise AssertionError('完成后不得继续')
    d = Relay()
    d.send('to-weasel', '完整任务书', disconnect=True)
    assert not d.receipts
    assert d.send('to-weasel', '完整任务书') == 'already-received'
    assert d.sends == 1 and len(d.receipts) == 1
    print('PASS: 相对链接、skill基本格式、四项模板/两段话、两轮继续与停止、断线已送达去重')

if __name__ == '__main__':
    main()
