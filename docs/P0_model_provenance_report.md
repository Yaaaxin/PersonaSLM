# P0 Model Provenance Report

2026-10-12；Research Protocol v1.1。本文区分本地二进制完整性、GGUF 自述元数据、公开制品身份和上游模型关系。第三方量化制品不等同于 Qwen 官方发布的 GGUF。

| 核验层级 | 状态 | 实际证据 | 限制 |
|---|---|---|---|
| File Integrity Verification | PASS | 本地 GGUF 为 1,270,808,256 bytes；计算的 SHA-256 与下列固定制品摘要一致；推理前后校验一致 | 仅证明文件一致性 |
| GGUF Metadata Verification | PASS | llama.cpp 实际加载并输出 GGUF V3、38 项元数据、320 tensors；`general.architecture=qwen35`、`general.name=Qwen Qwen3.5 2B Base`、`general.finetune=Base`、`general.file_type=15`，解析为 Q4_K Medium | 验证的是文件中的声明及加载结果，不能独立证明训练来源 |
| Published Artifact Identification | PASS | 研究者先提供固定 revision 并核验公开摘要；本轮于 `2026-10-12T17:08:23.161280+00:00` 另行从 Hugging Face 固定 revision API 获得 HTTP 200，目标文件的 `lfs.oid`、`lfs.size` 与本地一致 | API 核验锁定这一个第三方制品，不是量化保真度证明 |
| Upstream Model Lineage Verification | PARTIAL | 原始开发者为 Qwen，声明上游为 `Qwen/Qwen3.5-2B-Base`；官方模型说明明确为预训练模型；本地 Base/架构元数据相符 | 缺少第三方转换时使用的上游固定 revision、原始权重摘要、转换/量化工具版本及完整命令；未重新量化或比较 tensors |

## 固定制品

- Original developer / repository：Qwen / [Qwen/Qwen3.5-2B-Base](https://huggingface.co/Qwen/Qwen3.5-2B-Base)。官方页面的预训练说明支持 Base 用途；其通用模型表还包含 “Pre-training & Post-training” 字样，不能用该概括替代第三方文件来源证明。
- GGUF publisher / repository：aashish1904 / `aashish1904/Qwen3.5-2B-Base-GGUF`。
- 固定 revision：`765d2baaa04dbb8d6df3e78af571e6beaa4373d7`。
- 文件：`Qwen3.5-2B-Base.Q4_K_M.gguf`，1,270,808,256 bytes。
- SHA-256：`ab36f9a7b0194ed9a6f80eeb000dac73002bcb14d0397c11c39417b6cd814994`。
- [固定文件地址](https://huggingface.co/aashish1904/Qwen3.5-2B-Base-GGUF/blob/765d2baaa04dbb8d6df3e78af571e6beaa4373d7/Qwen3.5-2B-Base.Q4_K_M.gguf)；[固定 revision 的 API 目录](https://huggingface.co/api/models/aashish1904/Qwen3.5-2B-Base-GGUF/tree/765d2baaa04dbb8d6df3e78af571e6beaa4373d7)。API 返回的目标文件 Git pointer OID 是 `9a84b1a91de97eb455321f1e68dc8571d021d34e`；它与 LFS 二进制 SHA-256 是不同字段，不可混用。

## 实际加载与后端

详细加载证据位于本地 `results/p0_validation/20261012T164648/tokenizer_runs/20261012T165905-f06b3743414742079d0820d7714a6413/server.log`。后续控制条件运行各自保留相同类型的加载日志。

- 模型参数数目由后端报告为 1.88 B；24 层，embedding 2048，词表 248,320，训练上下文元数据 262,144。本次部署上下文固定为 4,096，两者不可混淆。
- Tensor 类型：f32 133、q4_K 152、q5_K 18、q6_K 17。Q4_K_M 是混合量化配置，不意味着所有 tensors 都是 4-bit。
- Tokenizer：BPE，`tokenizer.ggml.model=gpt2`、`tokenizer.ggml.pre=qwen35`；这是 tokenizer 类型标签，不是说加载了 GPT-2 模型。
- `tokenizer.ggml.add_bos_token=false`；EOS 248044 `<|endoftext|>`。后端还报告 BOS 11 `,`，但实际探针未自动插入 BOS；不能把 `/props` 中的 BOS 字符串误读为实际输入含逗号。
- 文件含 chat template，不据此推断为 Instruct。本次 native `/completion` 接收已冻结 Base transcript 的 IDs，没有调用 chat template。
- 后端：llama.cpp `0.6.0-dev (build 11573, commit 0f701c882)`，Clang 20.1.8 / Windows x86_64。
- `llama-server.exe` SHA-256：`71bbdc3c617532c217c31002044e11994cfe41baab2aa667a394ec74cc1db846`，本地计算与研究者提供的预期值一致。没有独立核验此可执行文件的发布签名或源码构建可重复性。
- `/props.model_path` 与配置文件路径一致，build/context 一致；受控子进程加载了该文件。路径、摘要和日志是相互佐证，不是对运行内存中所有 tensor 的独立摘要。

## 保留的来源核验失败

浏览工具不能打开第三方固定文件页及 README/API URL；原始 Qwen 官方模型页可读。Python 首次直连受沙箱限制，`WinError 10013`，退出 2。经批准在沙箱外执行一次公开元数据读取，API 返回 200，但同一 revision 的 README 返回 **HTTP 404**，因此该命令整体退出 **2**。没有掩盖 README 失败，也没有因 API 成功就宣称整个命令成功。

原始记录：本地验证目录内 `publisher_fetch_command.json`、`publisher_metadata.json`、`publisher_fetch_escalated_command.json`、`publisher_metadata_verified.json`。没有下载新模型，没有替换现有权重，没有重新运行不受来源补充影响的 C0。

**仍需人工或独立技术证据：**第三方量化所用上游 revision/权重摘要、转换与量化配方、工具版本和必要的校准数据说明；如要求验证保真度，需另行制定与原始模型的对照验证。本次没有执行该验证，不能标为 PASS。
