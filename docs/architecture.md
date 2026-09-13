# Architecture

The initial release preserves native-v4's **bidirectional byte encoder + fixed
ordinal query + final retrieval** design. LAPA is not inserted into every
Transformer layer, and this model is not a causal language model.

1. Byte embeddings and a task token enter the common encoder.
2. SDPA/RoPE/CoPE/TAPE determines encoder attention and final retrieval logits.
3. Source and factorized program heads infer distributions over byte positions
   and 68 ordered candidate programs.
4. A deterministic executor reads original bytes, resolves candidate endpoints,
   applies guards and checks bounds.
5. Source/program/gate mass is pushed forward to destination coordinates.
6. Invalid/unused mass goes to a neutral sink, redistributed over valid support.
7. The smoothed route density ratio is added to final retrieval logits.

Let R be valid route mass, eta = 1 - sum(R), and U the uniform distribution on
observed coordinates plus the two task endpoint classes. Then

```text
P     = R + eta * U
P_eps = (1 - epsilon) * P + epsilon * U
S     = backbone_logits + prior_strength * log(P_eps / U)
final = mean_heads(masked_softmax(S))
```

END and NULL have their own task-head logits; they are not bytes and have no
fabricated value vectors. The neutral sink is neither END nor NULL.

TAPE transports both positional streams using encoder attention weights and
updates them with the position MLP. CoPE shares one learned position table across
encoder blocks and retrieval; its encoder gate excludes the task key. These
stateful operations remain distinct from the final additive LAPA bias.

All backbone-private tensors are allocated in one graph to preserve legacy
checkpoint keys. LAPA off still permits source/program auxiliary training, but
never calls the byte executor or route fusion. Its `final` is the same tensor
object as `base`.
