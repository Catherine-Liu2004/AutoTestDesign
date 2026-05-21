<template>
  <div>
    <div class="page-header">
      <h2>Requirements & Risk Analysis</h2>
      <p>Review parsed structures, edit risk scores, and visualize state transitions.</p>
    </div>

    <!-- Stats bar -->
    <el-row :gutter="12" style="margin-bottom:16px">
      <el-col :span="6">
        <el-card body-style="padding:12px 16px" shadow="never" style="border:1px solid #e2e8f0">
          <div style="font-size:22px;font-weight:700;color:#1e293b">{{ requirements.length }}</div>
          <div style="font-size:12px;color:#64748b;margin-top:2px">Total Requirements</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card body-style="padding:12px 16px" shadow="never" style="border:1px solid #e2e8f0">
          <div style="font-size:22px;font-weight:700;color:#10b981">{{ parsedCount }}</div>
          <div style="font-size:12px;color:#64748b;margin-top:2px">Parsed</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card body-style="padding:12px 16px" shadow="never" style="border:1px solid #e2e8f0">
          <div style="font-size:22px;font-weight:700;color:#ef4444">{{ highRiskCount }}</div>
          <div style="font-size:12px;color:#64748b;margin-top:2px">High Risk</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card body-style="padding:12px 16px" shadow="never" style="border:1px solid #e2e8f0">
          <div style="font-size:22px;font-weight:700;color:#3b82f6">{{ diagramCount }}</div>
          <div style="font-size:12px;color:#64748b;margin-top:2px">State Diagrams</div>
        </el-card>
      </el-col>
    </el-row>

    <!-- Toolbar -->
    <el-card style="margin-bottom:16px" body-style="padding:12px 16px">
      <el-space>
        <el-button :icon="Refresh" @click="loadData" :loading="loading">Refresh</el-button>
        <el-button type="warning" :icon="MagicStick" @click="handleAnalyzeRisk" :loading="analyzing">
          Analyze Risk (AI)
        </el-button>
      </el-space>
    </el-card>

    <el-table :data="requirements" border stripe row-key="id">
      <el-table-column type="expand">
        <template #default="{ row }">
          <div style="padding:12px 24px">
            <el-descriptions :column="1" border size="small">
              <el-descriptions-item label="Full Requirement Text">
                <pre style="margin:0;white-space:pre-wrap;word-break:break-all">{{ row.raw_text }}</pre>
              </el-descriptions-item>
              <el-descriptions-item v-if="row.structured" label="Input Fields">
                {{ (row.structured.input_fields || []).join(', ') || '—' }}
              </el-descriptions-item>
              <el-descriptions-item v-if="row.structured" label="Conditions">
                <ul style="margin:0;padding-left:16px">
                  <li v-for="c in (row.structured.conditions || [])" :key="c">{{ c }}</li>
                </ul>
              </el-descriptions-item>
              <el-descriptions-item v-if="row.structured" label="Expected Actions">
                <ul style="margin:0;padding-left:16px">
                  <li v-for="a in (row.structured.expected_actions || [])" :key="a">{{ a }}</li>
                </ul>
              </el-descriptions-item>
              <el-descriptions-item v-if="row.risk_rationale" label="Risk Rationale">
                {{ row.risk_rationale }}
              </el-descriptions-item>
            </el-descriptions>
          </div>
        </template>
      </el-table-column>
      <el-table-column prop="id" label="ID" width="90">
        <template #default="{ row }">{{ row.id.slice(0, 8) }}</template>
      </el-table-column>
      <el-table-column prop="raw_text" label="Requirement Text" min-width="200">
        <template #default="{ row }">
          <span style="display:block;max-width:320px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;cursor:pointer" :title="'Click ▶ to expand'">
            {{ row.raw_text }}
          </span>
        </template>
      </el-table-column>
      <el-table-column label="Risk Score" width="110">
        <template #default="{ row }">
          <el-input-number
            v-model="row.risk_score"
            :min="0" :max="10" :precision="1" :step="0.5" size="small"
            @change="(v) => saveRisk(row, v)"
          />
        </template>
      </el-table-column>
      <el-table-column label="Priority" width="120">
        <template #default="{ row }">
          <el-tag :type="priorityType(row.priority)">{{ row.priority || '—' }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="Parsed" width="80">
        <template #default="{ row }">
          <el-icon :color="row.structured ? '#67C23A' : '#909399'">
            <Check v-if="row.structured" />
            <Close v-else />
          </el-icon>
        </template>
      </el-table-column>
      <el-table-column label="Actions" width="280">
        <template #default="{ row }">
          <el-button size="small" @click="parseOne(row)">Parse</el-button>
          <el-button size="small" type="primary" :disabled="!row.structured" @click="openStructureEdit(row)">Structure</el-button>
          <el-button size="small" type="success" @click="openStateDiagram(row)">Diagram</el-button>
          <el-button size="small" type="danger" @click="deleteOne(row)">Del</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- Structure Edit Dialog -->
    <el-dialog v-model="structureDialog" title="Edit Parsed Structure" width="700px" :close-on-click-modal="false">
      <el-form v-if="editRow" :model="editForm" label-width="140px">
        <el-form-item label="Input Fields">
          <div style="width:100%">
            <el-tag
              v-for="(tag, i) in editForm.input_fields"
              :key="i"
              closable
              @close="editForm.input_fields.splice(i, 1)"
              style="margin:2px"
            >{{ tag }}</el-tag>
            <el-input
              v-model="newInputField"
              size="small"
              placeholder="Add field…"
              style="width:140px;margin-left:4px"
              @keyup.enter="addTag('input_fields', 'newInputField')"
            />
            <el-button size="small" @click="addTag('input_fields', 'newInputField')" style="margin-left:4px">+</el-button>
          </div>
        </el-form-item>
        <el-form-item label="Data Ranges">
          <div style="width:100%">
            <div v-for="(val, key) in editForm.data_ranges" :key="key" style="margin-bottom:4px">
              <el-tag closable @close="deleteRange(key)" style="margin-right:4px">{{ key }}</el-tag>
              <el-input
                :model-value="val"
                @update:model-value="v => editForm.data_ranges[key] = v"
                size="small"
                style="width:220px"
                placeholder="range description"
              />
            </div>
            <div style="margin-top:4px">
              <el-input v-model="newRangeKey" size="small" placeholder="key" style="width:100px;margin-right:4px" />
              <el-input v-model="newRangeVal" size="small" placeholder="value" style="width:160px;margin-right:4px" />
              <el-button size="small" @click="addRange">+</el-button>
            </div>
          </div>
        </el-form-item>
        <el-form-item label="Conditions">
          <div style="width:100%">
            <el-tag
              v-for="(tag, i) in editForm.conditions"
              :key="i"
              closable
              @close="editForm.conditions.splice(i, 1)"
              style="margin:2px"
            >{{ tag }}</el-tag>
            <el-input
              v-model="newCondition"
              size="small"
              placeholder="Add condition…"
              style="width:200px;margin-left:4px"
              @keyup.enter="addTag('conditions', 'newCondition')"
            />
            <el-button size="small" @click="addTag('conditions', 'newCondition')" style="margin-left:4px">+</el-button>
          </div>
        </el-form-item>
        <el-form-item label="Expected Actions">
          <div style="width:100%">
            <el-tag
              v-for="(tag, i) in editForm.expected_actions"
              :key="i"
              closable
              @close="editForm.expected_actions.splice(i, 1)"
              style="margin:2px"
            >{{ tag }}</el-tag>
            <el-input
              v-model="newExpectedAction"
              size="small"
              placeholder="Add action…"
              style="width:200px;margin-left:4px"
              @keyup.enter="addTag('expected_actions', 'newExpectedAction')"
            />
            <el-button size="small" @click="addTag('expected_actions', 'newExpectedAction')" style="margin-left:4px">+</el-button>
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="structureDialog = false">Cancel</el-button>
        <el-button type="primary" :loading="saving" @click="saveStructure">Save</el-button>
      </template>
    </el-dialog>

    <!-- State Diagram Dialog -->
    <el-dialog v-model="diagramDialog" title="State Transition Diagram" width="760px">
      <div v-if="diagramLoading" v-loading="true" style="height:200px" />
      <div v-else-if="diagramMermaid">
        <el-alert type="info" :closable="false" style="margin-bottom:12px">
          <template #title>
            Mermaid diagram for: <strong>{{ diagramReqText }}</strong>
          </template>
        </el-alert>
        <div ref="mermaidContainer" style="background:#f5f7fa;padding:16px;border-radius:6px;overflow:auto;min-height:120px" />
        <el-divider />
        <el-input type="textarea" :model-value="diagramMermaid" readonly :rows="8" style="font-family:monospace;font-size:12px" />
      </div>
      <el-empty v-else description="No diagram yet" />
      <template #footer>
        <el-button :loading="diagramLoading" @click="generateDiagram">
          {{ diagramMermaid ? 'Regenerate' : 'Generate Diagram (AI)' }}
        </el-button>
        <el-button @click="diagramDialog = false">Close</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh, MagicStick } from '@element-plus/icons-vue'
import mermaid from 'mermaid'
import {
  listRequirements, analyzeRisk, parseRequirement, deleteRequirement,
  updateRisk, updateStructure, generateStateDiagram, getStateDiagram
} from '../api/index.js'

mermaid.initialize({ startOnLoad: false, theme: 'default' })

const requirements = ref([])
const loading = ref(false)
const analyzing = ref(false)
const saving = ref(false)

// computed stats
const parsedCount = computed(() => requirements.value.filter(r => r.structured).length)
const highRiskCount = computed(() => requirements.value.filter(r => r.priority === 'high').length)
const diagramCount = computed(() => requirements.value.filter(r => r.state_diagram).length)

// structure dialog state
const structureDialog = ref(false)
const editRow = ref(null)
const editForm = ref({ input_fields: [], data_ranges: {}, conditions: [], expected_actions: [] })
const newInputField = ref('')
const newCondition = ref('')
const newExpectedAction = ref('')
const newRangeKey = ref('')
const newRangeVal = ref('')

// state diagram dialog state
const diagramDialog = ref(false)
const diagramLoading = ref(false)
const diagramMermaid = ref('')
const diagramReqText = ref('')
const diagramReqId = ref('')
const mermaidContainer = ref(null)

const priorityType = (p) => ({ high: 'danger', medium: 'warning', low: 'success' }[p] || 'info')

async function loadData() {
  loading.value = true
  try {
    const { data } = await listRequirements()
    requirements.value = data
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    loading.value = false
  }
}

async function handleAnalyzeRisk() {
  analyzing.value = true
  try {
    const ids = requirements.value.map(r => r.id)
    await analyzeRisk(ids)
    ElMessage.success('Risk analysis complete')
    await loadData()
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    analyzing.value = false
  }
}

async function parseOne(row) {
  try {
    await parseRequirement(row.id)
    ElMessage.success('Parsed')
    await loadData()
  } catch (e) {
    ElMessage.error(e.message)
  }
}

async function deleteOne(row) {
  try {
    await deleteRequirement(row.id)
    ElMessage.success('Deleted')
    await loadData()
  } catch (e) {
    ElMessage.error(e.message)
  }
}

async function saveRisk(row, value) {
  try {
    await updateRisk(row.id, { risk_score: value })
  } catch (e) {
    ElMessage.error(e.message)
  }
}

function openStructureEdit(row) {
  editRow.value = row
  const s = row.structured || {}
  editForm.value = {
    input_fields: Array.isArray(s.input_fields) ? [...s.input_fields] : [],
    data_ranges: s.data_ranges ? { ...s.data_ranges } : {},
    conditions: Array.isArray(s.conditions) ? [...s.conditions] : [],
    expected_actions: Array.isArray(s.expected_actions) ? [...s.expected_actions] : [],
  }
  newInputField.value = ''
  newCondition.value = ''
  newExpectedAction.value = ''
  newRangeKey.value = ''
  newRangeVal.value = ''
  structureDialog.value = true
}

function addTag(field, varName) {
  const varMap = { input_fields: newInputField, conditions: newCondition, expected_actions: newExpectedAction }
  const ref = varMap[field]
  if (ref && ref.value.trim()) {
    editForm.value[field].push(ref.value.trim())
    ref.value = ''
  }
}

function addRange() {
  if (newRangeKey.value.trim()) {
    editForm.value.data_ranges[newRangeKey.value.trim()] = newRangeVal.value.trim()
    newRangeKey.value = ''
    newRangeVal.value = ''
  }
}

function deleteRange(key) {
  const d = { ...editForm.value.data_ranges }
  delete d[key]
  editForm.value.data_ranges = d
}

async function saveStructure() {
  saving.value = true
  try {
    await updateStructure(editRow.value.id, editForm.value)
    ElMessage.success('Structure saved')
    structureDialog.value = false
    await loadData()
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    saving.value = false
  }
}

async function openStateDiagram(row) {
  diagramReqId.value = row.id
  diagramReqText.value = row.raw_text.slice(0, 80)
  diagramMermaid.value = row.state_diagram || ''
  diagramDialog.value = true
  if (diagramMermaid.value) {
    // Wait for dialog open animation before rendering
    await new Promise(r => setTimeout(r, 300))
    await renderMermaid(diagramMermaid.value)
  }
}

async function generateDiagram() {
  diagramLoading.value = true
  try {
    const { data } = await generateStateDiagram(diagramReqId.value)
    diagramMermaid.value = data.mermaid
    diagramLoading.value = false          // flip v-if first
    await loadData()
    await renderMermaid(data.mermaid)
  } catch (e) {
    ElMessage.error(e.message)
    diagramLoading.value = false
  }
}

async function renderMermaid(code) {
  // Wait for v-else-if branch to mount — nextTick alone is not always enough
  // during dialog open animation or loading → content transition.
  await nextTick()
  if (!mermaidContainer.value) {
    await new Promise(r => setTimeout(r, 200))
    await nextTick()
  }
  if (!mermaidContainer.value) return
  try {
    mermaidContainer.value.innerHTML = ''
    const uid = `md-${Date.now()}`
    const { svg } = await mermaid.render(uid, code)
    mermaidContainer.value.innerHTML = svg
  } catch (e) {
    mermaidContainer.value.innerHTML = `<pre style="color:red">${e.message}</pre>`
  }
}

watch(diagramMermaid, async (val) => {
  if (val && diagramDialog.value) await renderMermaid(val)
})

onMounted(loadData)
</script>
