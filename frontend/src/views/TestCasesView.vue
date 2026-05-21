<template>
  <div>
    <div class="page-header">
      <h2>Test Case Generation</h2>
      <p>Select requirements and techniques to generate AI-powered test cases.</p>
    </div>

    <!-- 生成配置 -->
    <el-card style="margin-bottom:16px">
      <el-form label-width="160px">
        <el-form-item label="Select Requirements">
          <el-select v-model="selectedReqs" multiple placeholder="Select requirements" style="width:100%">
            <el-option v-for="r in requirements" :key="r.id" :label="r.raw_text.slice(0,80)" :value="r.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="Techniques">
          <el-checkbox-group v-model="techniques">
            <el-checkbox value="equivalence_partitioning">Equivalence Partitioning</el-checkbox>
            <el-checkbox value="boundary_value_analysis">Boundary Value Analysis</el-checkbox>
            <el-checkbox value="decision_table">Decision Table</el-checkbox>
            <el-checkbox value="state_transition">State Transition (Whitebox)</el-checkbox>
          </el-checkbox-group>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleGenerate" :loading="generating" :disabled="!selectedReqs.length">
            Generate Test Cases (AI)
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 上次生成的 Suite ID 提示 -->
    <el-alert
      v-if="lastSuiteId"
      type="success"
      :closable="false"
      style="margin-bottom:12px"
    >
      <template #title>
        Suite generated — ID:
        <el-text code style="font-size:13px">{{ lastSuiteId }}</el-text>
        <el-button link size="small" @click="copySuiteId" style="margin-left:8px">Copy</el-button>
        <el-button link size="small" type="warning" :loading="generatingOracle" @click="handleGenerateOracle" style="margin-left:16px">
          Generate Oracle (AI)
        </el-button>
        <el-button link size="small" type="info" :loading="optimizing" @click="handleOptimize" style="margin-left:8px">
          Optimize Suite
        </el-button>
        <el-text type="info" size="small" style="margin-left:16px">Go to Export page and select this suite to download.</el-text>
      </template>
    </el-alert>

    <!-- 测试用例表格 -->
    <el-table :data="testCases" border stripe v-loading="loading" row-key="id">
      <el-table-column type="expand">
        <template #default="{ row }">
          <div style="padding:12px 24px">
            <el-descriptions :column="1" border size="small">
              <el-descriptions-item label="Preconditions">{{ row.preconditions || '—' }}</el-descriptions-item>
              <el-descriptions-item label="Input Data">
                <pre style="margin:0;white-space:pre-wrap">{{ row.input_data ? JSON.stringify(row.input_data, null, 2) : '—' }}</pre>
              </el-descriptions-item>
              <el-descriptions-item label="Expected Result">{{ row.expected_result }}</el-descriptions-item>
              <el-descriptions-item label="Suite ID">{{ row.suite_id }}</el-descriptions-item>
            </el-descriptions>
          </div>
        </template>
      </el-table-column>
      <el-table-column prop="id" label="TC ID" width="90">
        <template #default="{ row }">{{ row.id.slice(0,8) }}</template>
      </el-table-column>
      <el-table-column prop="technique" label="Technique" width="140" />
      <el-table-column prop="title" label="Title" min-width="200" show-overflow-tooltip>
        <template #default="{ row }">
          <span style="display:block;max-width:300px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;cursor:pointer" title="Click ▶ to expand">
            {{ row.title }}
          </span>
        </template>
      </el-table-column>
      <el-table-column label="Priority" width="100">
        <template #default="{ row }">
          <el-tag :type="priorityType(row.priority)">{{ row.priority }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="Status" width="120">
        <template #default="{ row }">
          <el-select v-model="row.status" size="small" @change="(v) => saveStatus(row, v)">
            <el-option value="pending" label="Pending" />
            <el-option value="pass" label="Pass" />
            <el-option value="fail" label="Fail" />
          </el-select>
        </template>
      </el-table-column>
      <el-table-column label="Actions" width="120">
        <template #default="{ row }">
          <el-button link size="small" type="primary" @click="openEdit(row)">Edit</el-button>
          <el-popconfirm title="Delete this test case?" @confirm="handleDelete(row)">
            <template #reference>
              <el-button link size="small" type="danger">Delete</el-button>
            </template>
          </el-popconfirm>
        </template>
      </el-table-column>
    </el-table>

    <!-- 编辑对话框 -->
    <el-dialog v-model="editVisible" title="Edit Test Case" width="640px">
      <el-form v-if="editForm" :model="editForm" label-width="140px">
        <el-form-item label="Title">
          <el-input v-model="editForm.title" />
        </el-form-item>
        <el-form-item label="Preconditions">
          <el-input v-model="editForm.preconditions" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="Input Data (JSON)">
          <el-input v-model="editForm.inputDataStr" type="textarea" :rows="3" placeholder='{"field": "value"}' />
        </el-form-item>
        <el-form-item label="Expected Result">
          <el-input v-model="editForm.expected_result" type="textarea" :rows="3" />
        </el-form-item>
        <el-form-item label="Priority">
          <el-select v-model="editForm.priority">
            <el-option value="high" label="High" />
            <el-option value="medium" label="Medium" />
            <el-option value="low" label="Low" />
          </el-select>
        </el-form-item>
        <el-form-item label="Status">
          <el-select v-model="editForm.status">
            <el-option value="pending" label="Pending" />
            <el-option value="pass" label="Pass" />
            <el-option value="fail" label="Fail" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editVisible = false">Cancel</el-button>
        <el-button type="primary" @click="saveEdit" :loading="saving">Save</el-button>
      </template>
    </el-dialog>

    <!-- Traceability Matrix & Strategy Panel (visible when a suite is selected) -->
    <el-card v-if="lastSuiteId" style="margin-top:20px">
      <template #header>
        <div style="display:flex;justify-content:space-between;align-items:center">
          <span>Coverage Strategy &amp; Traceability Matrix</span>
          <el-button type="primary" link @click="loadTraceability">Refresh Matrix</el-button>
        </div>
      </template>

      <!-- Strategy re-select -->
      <el-form label-width="160px" style="margin-bottom:16px">
        <el-form-item label="Update Techniques">
          <el-checkbox-group v-model="strategyTechniques">
            <el-checkbox value="equivalence_partitioning">Equivalence Partitioning</el-checkbox>
            <el-checkbox value="boundary_value_analysis">Boundary Value Analysis</el-checkbox>
            <el-checkbox value="decision_table">Decision Table</el-checkbox>
            <el-checkbox value="state_transition">State Transition (Whitebox)</el-checkbox>
          </el-checkbox-group>
        </el-form-item>
        <el-form-item>
          <el-button
            type="warning"
            :loading="regenerating"
            :disabled="!strategyTechniques.length"
            @click="handleUpdateStrategy"
          >
            Regenerate with New Strategy
          </el-button>
        </el-form-item>
      </el-form>

      <!-- Traceability matrix table -->
      <el-divider>Traceability Matrix (Req → Test Cases)</el-divider>
      <el-table v-if="traceabilityRows.length" :data="traceabilityRows" border stripe>
        <el-table-column prop="req_id" label="Requirement ID" width="160">
          <template #default="{ row }">
            <el-text code>{{ row.req_id.slice(0, 8) }}</el-text>
          </template>
        </el-table-column>
        <el-table-column prop="req_text" label="Requirement" show-overflow-tooltip />
        <el-table-column prop="tc_count" label="TC Count" width="100" />
        <el-table-column label="Test Case IDs">
          <template #default="{ row }">
            <el-tag
              v-for="tcId in row.tc_ids"
              :key="tcId"
              size="small"
              style="margin:2px"
            >{{ tcId.slice(0, 8) }}</el-tag>
          </template>
        </el-table-column>
      </el-table>
      <el-empty v-else description="No traceability data. Click Refresh Matrix." />
    </el-card>

    <!-- Oracle Results Dialog -->
    <el-dialog v-model="oracleVisible" title="AI Test Oracle Results" width="760px">
      <el-table :data="oracleResults" border stripe>
        <el-table-column prop="tc_id" label="TC ID" width="100">
          <template #default="{ row }">{{ row.tc_id.slice(0, 8) }}</template>
        </el-table-column>
        <el-table-column prop="original_expected" label="Original Expected" show-overflow-tooltip />
        <el-table-column prop="ai_oracle" label="AI Oracle" show-overflow-tooltip />
      </el-table>
      <template #footer>
        <el-button type="primary" @click="oracleVisible = false">Close</el-button>
      </template>
    </el-dialog>

    <!-- Optimize Suite Dialog -->
    <el-dialog v-model="optimizeVisible" title="Test Suite Optimization" width="760px">
      <el-form inline style="margin-bottom:12px">
        <el-form-item label="Strategy">
          <el-select v-model="optimizeStrategy" size="small">
            <el-option value="risk_based" label="Risk-Based" />
            <el-option value="coverage_efficiency" label="Coverage Efficiency" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button size="small" :loading="optimizing" @click="handleOptimize">Re-analyze</el-button>
        </el-form-item>
      </el-form>
      <el-alert
        v-if="optimizeCandidates.length === 0"
        type="success"
        title="No redundant test cases found — suite looks optimal!"
        :closable="false"
      />
      <el-table
        v-else
        :data="optimizeCandidates"
        border
        @selection-change="rows => selectedForRemoval = rows.map(r => r.tc_id)"
      >
        <el-table-column type="selection" width="50" />
        <el-table-column prop="tc_id" label="TC ID" width="100">
          <template #default="{ row }">{{ row.tc_id.slice(0, 8) }}</template>
        </el-table-column>
        <el-table-column prop="title" label="Title" show-overflow-tooltip />
        <el-table-column prop="reason" label="Reason" show-overflow-tooltip />
      </el-table>
      <template #footer>
        <el-button @click="optimizeVisible = false">Cancel</el-button>
        <el-button
          type="danger"
          :disabled="selectedForRemoval.length === 0"
          @click="confirmRemoval"
        >
          Remove Selected ({{ selectedForRemoval.length }})
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import {
  listRequirements, generateTestCases, listTestCases,
  updateTestCase, deleteTestCase, getTraceability, updateStrategy,
  generateOracle, optimizeSuite
} from '../api/index.js'

const requirements = ref([])
const testCases = ref([])
const selectedReqs = ref([])
const techniques = ref(['equivalence_partitioning', 'boundary_value_analysis', 'decision_table'])
const loading = ref(false)
const generating = ref(false)
const lastSuiteId = ref('')

// edit dialog
const editVisible = ref(false)
const editForm = ref(null)
const saving = ref(false)

// traceability & strategy
const traceabilityRows = ref([])
const strategyTechniques = ref(['equivalence_partitioning', 'boundary_value_analysis', 'decision_table'])
const regenerating = ref(false)

// oracle
const oracleResults = ref([])
const generatingOracle = ref(false)
const oracleVisible = ref(false)

// optimize
const optimizeCandidates = ref([])
const optimizing = ref(false)
const optimizeVisible = ref(false)
const selectedForRemoval = ref([])
const optimizeStrategy = ref('risk_based')

const priorityType = (p) => ({ high: 'danger', medium: 'warning', low: 'success' }[p] || 'info')

async function loadRequirements() {
  const { data } = await listRequirements()
  requirements.value = data
}

async function loadTestCases() {
  loading.value = true
  try {
    const { data } = await listTestCases()
    testCases.value = data
  } finally {
    loading.value = false
  }
}

async function handleGenerate() {
  if (!techniques.value.length) return ElMessage.warning('Select at least one technique')
  generating.value = true
  try {
    const includeWhitebox = techniques.value.includes('state_transition')
    const techs = techniques.value.filter(t => t !== 'state_transition')
    const { data } = await generateTestCases({
      req_ids: selectedReqs.value,
      techniques: techs,
      include_whitebox: includeWhitebox,
    })
    lastSuiteId.value = data.id
    strategyTechniques.value = [...techniques.value]
    ElMessage.success(`Generated ${data.tc_count} test case(s)`)
    await loadTestCases()
    await loadTraceability()
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    generating.value = false
  }
}

async function loadTraceability() {
  if (!lastSuiteId.value) return
  try {
    const { data } = await getTraceability(lastSuiteId.value)
    // Enrich rows with req text
    const reqMap = Object.fromEntries(requirements.value.map(r => [r.id, r.raw_text]))
    traceabilityRows.value = Object.entries(data.matrix).map(([req_id, tc_ids]) => ({
      req_id,
      req_text: (reqMap[req_id] || req_id).slice(0, 100),
      tc_ids,
      tc_count: tc_ids.length,
    }))
  } catch (e) {
    ElMessage.error('Failed to load traceability: ' + e.message)
  }
}

async function handleUpdateStrategy() {
  if (!lastSuiteId.value) return
  regenerating.value = true
  try {
    const techs = strategyTechniques.value
    const { data } = await updateStrategy(lastSuiteId.value, techs)
    ElMessage.success(`Strategy updated — ${data.tc_count} test case(s) generated`)
    await loadTestCases()
    await loadTraceability()
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    regenerating.value = false
  }
}

async function handleGenerateOracle() {
  const ids = testCases.value.map(tc => tc.id)
  if (!ids.length) return ElMessage.warning('No test cases loaded')
  generatingOracle.value = true
  try {
    const { data } = await generateOracle(ids)
    oracleResults.value = data.results
    oracleVisible.value = true
    ElMessage.success(`Oracle generated for ${data.results.length} test case(s)`)
    await loadTestCases() // refresh to show ai_oracle in table
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    generatingOracle.value = false
  }
}

async function handleOptimize() {
  if (!lastSuiteId.value) return ElMessage.warning('Generate a suite first')
  optimizing.value = true
  try {
    const { data } = await optimizeSuite(lastSuiteId.value, optimizeStrategy.value)
    optimizeCandidates.value = data.candidates
    selectedForRemoval.value = data.candidates.map(c => c.tc_id)
    optimizeVisible.value = true
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    optimizing.value = false
  }
}

async function confirmRemoval() {
  let removed = 0
  for (const tcId of selectedForRemoval.value) {
    try {
      await deleteTestCase(tcId)
      removed++
    } catch (e) { /* skip */ }
  }
  optimizeVisible.value = false
  ElMessage.success(`Removed ${removed} test case(s)`)
  await loadTestCases()
}

async function saveStatus(row, v) {
  try {
    await updateTestCase(row.id, { status: v })
  } catch (e) {
    ElMessage.error(e.message)
  }
}

function openEdit(row) {
  editForm.value = {
    id: row.id,
    title: row.title,
    preconditions: row.preconditions || '',
    inputDataStr: row.input_data ? JSON.stringify(row.input_data, null, 2) : '',
    expected_result: row.expected_result,
    priority: row.priority,
    status: row.status,
  }
  editVisible.value = true
}

async function saveEdit() {
  saving.value = true
  try {
    let input_data = undefined
    if (editForm.value.inputDataStr.trim()) {
      try {
        input_data = JSON.parse(editForm.value.inputDataStr)
      } catch {
        return ElMessage.error('Input Data must be valid JSON')
      }
    }
    await updateTestCase(editForm.value.id, {
      title: editForm.value.title,
      preconditions: editForm.value.preconditions || null,
      input_data,
      expected_result: editForm.value.expected_result,
      priority: editForm.value.priority,
      status: editForm.value.status,
    })
    editVisible.value = false
    await loadTestCases()
    ElMessage.success('Saved')
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    saving.value = false
  }
}

async function handleDelete(row) {
  try {
    await deleteTestCase(row.id)
    testCases.value = testCases.value.filter(tc => tc.id !== row.id)
    ElMessage.success('Deleted')
  } catch (e) {
    ElMessage.error(e.message)
  }
}

function copySuiteId() {
  navigator.clipboard.writeText(lastSuiteId.value).then(() => ElMessage.success('Suite ID copied'))
}

onMounted(() => {
  loadRequirements()
  loadTestCases()
})
</script>
