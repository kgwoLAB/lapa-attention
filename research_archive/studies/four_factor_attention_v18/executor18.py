"""Parameter-free execution for source x width x endian x base attention.

This module contains no Q/K projections, learned parameters, program logits,
program classifier, signedness selector, or mask selector. The caller predicts
the four factors; this executor enumerates their fixed Cartesian support.
The only learned axes outside source are width, endian and the seven fixed
base-operator families below. ``packet_absolute_masked14`` includes its mask
and guard as *fixed operator semantics*, not as an independently inferred axis.

The existing package's numerical executor implements the 42 legal combinations
of the 4 x 2 x 7 Cartesian grid. Its internal flat list is an implementation
detail for deterministic execution, not a categorical model output. Illegal
width/base combinations remain explicit zero-validity cells in the full grid.
SMB2 companion reads and genuine NULL semantics are preserved exactly.

Forward takes only ModelInputs: bytes, observed mask and an unused public slot.
Training-label conversion is exposed separately and never called by forward.
END/NULL are stored at padded_length and padded_length+1; END's native numeric
location remains each sample's observed length, following the shared package.
"""

from dataclasses import dataclass
import hashlib
import json
from numbers import Integral

import torch
from torch import nn

from lapa.programs.bank import ProgramBank, native_bank as make_native_bank
from lapa.programs.executor import execute as execute_native
from lapa.programs.schema import Program
from lapa.types import ModelInputs


WIDTHS = (1, 2, 3, 4)
ENDIANS = ('big', 'little')
BASES = (
    'field_end_forward',
    'packet_absolute',
    'field_start_forward',
    'field_start_backward',
    'previous_offset_plus_length',
    'offset_with_next_length',
    'packet_absolute_masked14',
)
WIDTH_TO_ID = {value: index for index, value in enumerate(WIDTHS)}
ENDIAN_TO_ID = {value: index for index, value in enumerate(ENDIANS)}
BASE_TO_ID = {value: index for index, value in enumerate(BASES)}
FACTOR_NAMES = ('width', 'endian', 'base')
FACTOR_SHAPE = (len(WIDTHS), len(ENDIANS), len(BASES))
MASKED14_MASK = 0x3fff
MASKED14_GUARD_MASK = 0xc000
MASKED14_GUARD_VALUE = 0xc000


@dataclass(frozen=True)
class FourFactorExecution:
    """Every tensor is [batch, source, width=4, endian=2, base=7]."""

    target: torch.Tensor
    valid: torch.Tensor
    candidate_mask: torch.Tensor
    decoded: torch.Tensor
    null: torch.Tensor


def _operator(width, endian, base):
    """Return the fixed legal numerical operator, or None for an illegal cell."""
    if base == 'packet_absolute_masked14':
        if width != 2:
            return None
        return Program(width=2, endian=endian, base='packet_absolute',
                       mask=MASKED14_MASK, guard_mask=MASKED14_GUARD_MASK,
                       guard_value=MASKED14_GUARD_VALUE)
    if base in ('previous_offset_plus_length', 'offset_with_next_length') and width not in (2, 4):
        return None
    return Program(width=width, endian=endian, base=base, signed=False)


def native_program_to_axes(native_program_or_id, native_bank=None):
    """Convert a *training label* to (width_id, endian_id, base_id).

    A native integer label uses the exact supplied native bank, or the common
    package's stable native_v4 bank by default. Passing a Program object avoids
    integer-bank ambiguity. Signed operators and unsupported mask/guard/
    scale/shift/bias variants are rejected rather than silently approximated.
    This function has no role in prediction or choosing a source position.
    """
    if isinstance(native_program_or_id, Integral) and not isinstance(native_program_or_id, bool):
        bank = make_native_bank() if native_bank is None else native_bank
        index = int(native_program_or_id)
        if not 0 <= index < len(bank):
            raise ValueError(f'native program ID outside supplied bank: {index}')
        program = bank.programs[index]
    elif isinstance(native_program_or_id, Program):
        program = native_program_or_id
    else:
        raise TypeError('expected a native Program or integer program ID')
    if program.signed:
        raise ValueError('signed programs are outside the four-factor real-protocol operator support')
    if program.shift != 0 or program.scale != 1 or program.bias != 0:
        raise ValueError('shift, scale and bias variants are outside the fixed four-factor support')
    if program.mask is None:
        if program.guard_mask != 0 or program.guard_value != 0:
            raise ValueError('unmasked guarded programs are not in this operator support')
        base = program.base
    elif (program.width == 2 and program.base == 'packet_absolute'
          and program.mask == MASKED14_MASK
          and program.guard_mask == MASKED14_GUARD_MASK
          and program.guard_value == MASKED14_GUARD_VALUE):
        base = 'packet_absolute_masked14'
    else:
        raise ValueError('unsupported masked program; only fixed guarded packet-absolute masked14 is supported')
    if program.width not in WIDTH_TO_ID or program.endian not in ENDIAN_TO_ID or base not in BASE_TO_ID:
        raise ValueError('native program attributes are outside the four-factor support')
    candidate = _operator(program.width, program.endian, base)
    if candidate is None or candidate != program:
        raise ValueError('native program has no exact four-factor operator equivalent')
    return WIDTH_TO_ID[program.width], ENDIAN_TO_ID[program.endian], BASE_TO_ID[base]


class FourFactorExecutor(nn.Module):
    """Fixed raw-byte operator with 4 x 2 x 7 output axes and no parameters.

    API:
        execution = executor(inputs)
        execution = executor.execute(data, observed)
        wi, ei, bi = executor.native_to_axes(native_program_or_id)
        axis_targets = executor.native_labels_to_axes(native_label_tensor)

    ``axis_targets[..., 3]`` converts source-independent supervised labels;
    the true source index stays a separate training label. Both label-conversion
    helpers reject unsupported operators and never participate in forward.
    """

    widths = WIDTHS
    endians = ENDIANS
    bases = BASES
    factor_shape = FACTOR_SHAPE
    axis_names = FACTOR_NAMES

    def __init__(self):
        super().__init__()
        operators = []
        grid_index = torch.zeros(FACTOR_SHAPE, dtype=torch.long)
        grid_legal = torch.zeros(FACTOR_SHAPE, dtype=torch.bool)
        for wi, width in enumerate(WIDTHS):
            for ei, endian in enumerate(ENDIANS):
                for bi, base in enumerate(BASES):
                    operator = _operator(width, endian, base)
                    if operator is not None:
                        grid_index[wi, ei, bi] = len(operators)
                        grid_legal[wi, ei, bi] = True
                        operators.append(operator)
        assert len(operators) == 42 and int(grid_legal.sum()) == 42
        self.operator_bank = ProgramBank(tuple(operators), name='four_factor_fixed_v18',
                                        axis_names=FACTOR_NAMES)
        self.register_buffer('grid_operator_index', grid_index)
        self.register_buffer('grid_legal', grid_legal)

        # Compatibility metadata for native training labels, never predictions.
        native_bank = make_native_bank()
        self.native_bank_fingerprint = native_bank.fingerprint
        lookup = torch.full((len(native_bank), 3), -1, dtype=torch.long)
        for index, program in enumerate(native_bank.programs):
            try:
                lookup[index] = torch.tensor(native_program_to_axes(program))
            except ValueError:
                pass
        self.register_buffer('native_axis_lookup', lookup)

    def manifest(self):
        return dict(schema='lapa-four-factor-executor-v18', factor_axes=list(FACTOR_NAMES),
                    widths=list(WIDTHS), endians=list(ENDIANS), bases=list(BASES),
                    factor_shape=list(FACTOR_SHAPE), legal_cells=int(self.grid_legal.sum()),
                    signed_selector=False, mask_selector=False, program_classifier=False,
                    operator_bank=self.operator_bank.manifest(),
                    native_bank_fingerprint=self.native_bank_fingerprint,
                    masked14=dict(width=2, mask=MASKED14_MASK,
                                  guard_mask=MASKED14_GUARD_MASK, guard_value=MASKED14_GUARD_VALUE),
                    prior='fixed unsigned base operators, guarded masked14 and adjacent-field NULL semantics')

    @property
    def fingerprint(self):
        return hashlib.sha256(json.dumps(self.manifest(), sort_keys=True).encode()).hexdigest()

    @staticmethod
    def native_to_axes(native_program_or_id, native_bank=None):
        return native_program_to_axes(native_program_or_id, native_bank)

    def native_labels_to_axes(self, labels):
        if not isinstance(labels, torch.Tensor) or labels.dtype != torch.long:
            raise TypeError('native labels must be an int64 tensor')
        if labels.device != self.native_axis_lookup.device:
            raise ValueError('move executor and labels to the same device before conversion')
        if bool(((labels < 0) | (labels >= len(self.native_axis_lookup))).any()):
            raise ValueError('native labels outside the fixed compatibility bank')
        mapped = self.native_axis_lookup[labels]
        if bool((mapped < 0).any()):
            raise ValueError('native label contains unsupported signed/masked/modified operator')
        return mapped

    def forward(self, inputs):
        if not isinstance(inputs, ModelInputs):
            raise TypeError('executor forward accepts ModelInputs only, never labels or metadata')
        return self.execute(inputs.data, inputs.observed)

    def execute(self, data, observed):
        if data.ndim != 2 or data.dtype != torch.long:
            raise ValueError('data must be int64 [batch, length]')
        if observed.shape != data.shape or observed.dtype != torch.bool:
            raise ValueError('observed must be bool with data shape')
        if data.shape[0] < 1 or data.shape[1] < 1:
            raise ValueError('nonempty batch and byte storage required')
        if data.device != observed.device or data.device != self.grid_operator_index.device:
            raise ValueError('executor, data and observed must share a device')
        native = execute_native(self.operator_bank, data, observed)
        batch, length = data.shape
        legal = self.grid_legal[None, None]
        shape = (batch, length, *FACTOR_SHAPE)
        indices = self.grid_operator_index.flatten()
        gathered = {name: getattr(native, name).index_select(-1, indices).reshape(shape)
                    for name in ('target', 'valid', 'candidate_mask', 'decoded', 'null')}
        valid = gathered['valid'] & legal
        target = gathered['target'].masked_fill(~valid, 0)
        candidate_mask = gathered['candidate_mask'] & legal
        null = gathered['null'] & valid
        # The package's provisional incomplete-read value can reflect clamped
        # or padded reads. Do not expose that implementation artifact as data.
        source = torch.arange(length, device=data.device)[None, :, None, None, None]
        widths = torch.tensor(WIDTHS, device=data.device)[None, None, :, None, None]
        lengths = observed.sum(-1)[:, None, None, None, None]
        complete_read = observed[:, :, None, None, None] & (source + widths <= lengths)
        decoded = gathered['decoded'].masked_fill(~(complete_read & legal), 0)
        return FourFactorExecution(target, valid, candidate_mask, decoded, null)


def check_real_training_fields(data_root, device='cpu'):
    """Read only first two canonical TRAIN packets per real protocol.

    This bounded unit check compares factorized labels/execution to native
    labels/execution on all fields in those messages. It does not train, select
    an architecture, read evaluation data or create output files.
    """
    from pathlib import Path
    from lapa.data.collate import collate_slots

    root = Path(data_root)
    clean = {row['message_id']: row for row in map(json.loads, (root / 'clean/train.jsonl').read_text().splitlines())}
    gold = list(map(json.loads, (root / 'gold/train.jsonl').read_text().splitlines()))
    examples = []
    for protocol in ('dns', 'modbus', 'tls', 'smb2'):
        chosen = [row for row in gold if row['protocol'] == protocol][:2]
        if len(chosen) != 2:
            raise AssertionError(f'two train messages required for {protocol}')
        examples += [dict(row, data_hex=clean[row['message_id']]['data_hex'],
                          fields=sorted(row['fields'], key=lambda f: (f['start'], f['end'], f['semantic'])))
                     for row in chosen]
    native_bank = make_native_bank()
    samples = [(row, slot) for row in examples for slot in range(len(row['fields']))]
    batch = collate_slots(samples, native_bank).to(device)
    executor = FourFactorExecutor().to(device)
    assert not list(executor.parameters())
    result = executor(batch.inputs)
    wi, ei, bi = executor.native_labels_to_axes(batch.labels.programs).unbind(-1)
    i = torch.arange(len(samples), device=device)
    selected = (i, batch.labels.sources, wi, ei, bi)
    assert result.valid[selected].all()
    assert torch.equal(result.target[selected], batch.labels.targets)
    native = execute_native(native_bank, batch.inputs.data, batch.inputs.observed)
    native_selected = (i, batch.labels.sources, batch.labels.programs)
    assert torch.equal(result.target[selected], native.target[native_selected])
    assert torch.equal(result.null[selected], native.null[native_selected])
    assert torch.equal(result.decoded[selected], native.decoded[native_selected])

    # Added storage padding does not introduce bytes or move real destinations.
    import torch.nn.functional as F
    old_length = batch.inputs.data.shape[1]
    padded = ModelInputs(F.pad(batch.inputs.data, (0, 7), value=255),
                         F.pad(batch.inputs.observed, (0, 7), value=False), batch.inputs.slots)
    padded_result = executor(padded)
    original_targets = padded_result.target[:, :old_length]
    aligned_targets = torch.where(original_targets == old_length + 7, old_length,
                                  torch.where(original_targets == old_length + 8, old_length + 1, original_targets))
    assert torch.equal(result.target, aligned_targets)
    for name in ('valid', 'candidate_mask', 'decoded', 'null'):
        assert torch.equal(getattr(result, name), getattr(padded_result, name)[:, :old_length]), name
    assert not padded_result.valid[:, old_length:].any()
    assert not result.valid.masked_select(~executor.grid_legal[None, None].expand_as(result.valid)).any()
    # At width 1, endian is unidentifiable: both legal alternatives execute
    # identically. Training labels canonically use the native bank's big endian.
    assert torch.equal(result.target[:, :, 0, 0], result.target[:, :, 0, 1])
    assert torch.equal(result.valid[:, :, 0, 0], result.valid[:, :, 0, 1])
    for unsupported in (Program(1, 'big', 'packet_absolute', signed=True),
                        Program(2, 'big', 'field_start_forward', mask=MASKED14_MASK,
                                guard_mask=MASKED14_GUARD_MASK, guard_value=MASKED14_GUARD_VALUE)):
        try:
            executor.native_to_axes(unsupported)
        except ValueError:
            pass
        else:
            raise AssertionError('unsupported native operator was silently converted')
    return dict(status='PASS', device=device, train_messages=len(examples), train_fields=len(samples),
                evaluation_data_read=False, learnable_parameters=0, factor_shape=list(FACTOR_SHAPE),
                legal_combinations=int(executor.grid_legal.sum()),
                base_operators=list(BASES), padding_invariant=True, endian_width1_equivalent=True,
                exact_native_targets_and_null=True,
                target_kinds=dict(END=int((batch.labels.targets == old_length).sum()),
                                  NULL=int((batch.labels.targets == old_length + 1).sum()),
                                  INTERIOR=int((batch.labels.targets < old_length).sum())),
                fingerprint=executor.fingerprint)


if __name__ == '__main__':
    import argparse
    from pathlib import Path
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-root', default=str(Path(__file__).resolve().parent.parent / 'formula_search_v16/data'))
    parser.add_argument('--device', choices=('cpu', 'cuda'), default='cpu')
    args = parser.parse_args()
    torch.set_num_threads(2)
    print(json.dumps(check_real_training_fields(args.data_root, args.device), indent=2, sort_keys=True))
