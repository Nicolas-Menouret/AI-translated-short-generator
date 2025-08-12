import yaml
from jinja2 import Template


class PromptManager:
    def __init__(self, config_path="configs/prompts.yaml"):
        with open(config_path) as f:
            self.config = yaml.safe_load(f)

    def render(self, prompt_name: str, variables: dict):
        prompt_cfg = self.config[prompt_name]

        with open(prompt_cfg["path"], "r", encoding="utf-8") as f:
            prompt_template = Template(f.read())

        prompt_text = prompt_template.render(**variables)

        with open(prompt_cfg["base_prompt"]) as f:
            base_prompt = f.read()

        return {
            "base_prompt": base_prompt,
            "task_prompt": prompt_text,
            "model": prompt_cfg.get("model", "gpt-4.1"),
            "temperature": prompt_cfg.get("temperature", 0.7),
        }
