<template>
  <div>
    <div class="page-header">
      <h2>Test Case Generation</h2>
      <p>Select requirements and techniques to generate AI-powered test cases.</p>
    </div>

    <!-- Generation config -->
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

    <!-- Suites List -->
    <el-card>
      <template #header>
        <div style="display:flex;justify-content:space-between;align-items:center">
          <span>Test Suites <el-tag size="small" style="margin-left:6px">{{ suites.length }}</el-tag></span>
          <el-button link @click="loadSuites" :loading="loading">Refresh</el-button>
        </div>
      </template>

      <el-empty v-if="!loading && !suites.length" description="No suites yet. Generate test cases above." />

      <el-collapse v-model="activePanels" v-loading="loading">
        <el-collapse-item v-for="suite in suites" :key="suite.id" :name="suite.id">
          <template #title>
            <div style="display:flex;align-items:center;gap:8px;width:100%;padding-right:16px;min-width:0">
              <el-text code style="font-size:12px;flex-shrink:0">{{ suite.id.slice(0,8) }}</el-text>
              <span style="font-weight:500;flex-shrink:0">{{ suite.name }}</span>
              <el-tag size="small" type="primary" style="flex-shrink:0">{{ suite.tc_count }} TCs</el-tag>
              <el-tag
                v-for="t in suite.techniques"
                :key="t"
                size="small"
                type="info"
                style="margin:0 2px;flex-shrink:0"
              >{{ t.replace(/_/g, ' ') }}</el-tag>
              <span style="margin-left:auto;color:#999;font-size:12px;flex-shrink:0">{{ formatDate(suite.created_at) }}</span>
            </div>
          </template>

          <!-- Suite action buttons -->
          <div style="margin-bottom:12px;display:flex;gap:8px;flex-wrap:wrap;align-items:center">
            <el-button size="small" type="warning" @click="selectSuite(suite)">
              Traceability / Strategy
            </el-button>
            <el-button
              size="small"
              type="info"
              :loading="generatingOracle && activeSuiteId === suite.id"
              @click="handleGenerateOracle(suite)"
            >
              Generate Oracle
            </el-button>
            <el-button
              size="small"
              :loading="optimizing && activeSuiteId === suite.id"
              @click="handleOptimize(suite)"
            >
              Optimize Suite
            </el-button>
            <el-popconfirm
              :title="`Delete suite and all ${suite.tc_count} test case(s)?`"
              confirm-button-text="Delete"
              confirm-button-type="danger"
              @confirm="handleDeleteSuite(suite)"
            >
              <template #reference>
                <el-button size="small" type="danger">Delete Suite</el-button>
              </template>
            </el-popconfirm>
          </div>

          <!-- Test cases table for this suite -->
          <el-table :data="suite.test_cases" border stripe row-key="id" size="small">
            <el-table-column type="expand">
              <template #default="{ row }">
                <div style="padding:12px 24px">
                  <el-descriptions :column="1" border size="small">
                    <el-descriptions-item label="Preconditions">{{ row.preconditions || '—' }}</el-descriptions-item>
                    <el-descriptions-item label="Input Data">
                      <pre style="margin:0;white-space:pre-wrap">{{ row.input_data ? JSON.stringify(row.input_data, null, 2) : '—' }}</pre>
                    </el-descriptions-item>
                    <el-descriptions-item label="Expected Result">{{ row.expected_result }}</el-descriptions-item>
                    <el-descriptions-item v-if="row.ai_oracle" label="AI Oracle">{{ row.ai_oracle }}</el-descriptions-item>
                  </el-descriptions>
                </div>
              </template>
            </el-table-column>
            <el-table-column prop="id" label="TC ID" width="90">
              <template #default="{ row }">{{ row.id.slice(0,8) }}</template>
            </el-table-column>
            <el-table-column prop="technique" label="Technique" width="150" />
            <el-table-column prop="title" label="Title" min-width="200" show-overflow-tooltip />
            <el-table-column label="Priority" width="100">
              <template #default="{ row }">
                <el-tag :type="priorityType(row.priority)">{{ row.priority }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="Status" width="130">
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
                <el-popconfirm title="Delete this test case?" @confirm="handleDeleteCase(row, suite)">
                  <template #reference>
                    <el-button link size="small" type="danger">Delete</el-button>
                  </template>
                </el-popconfirm>
              </template>
            </el-table-column>
          </el-table>
        </el-collapse-item>
      </el-collapse>
    </el-card>

    <!-- Traceability Matrix & Strategy Panel -->
    <el-card v-if="activeSuiteId" style="margin-top:20px">
      <template #header>
        <div style="display:flex;justify-content:space-between;align-items:center">
          <span>
            Coverage Strategy &amp; Traceability —
            <el-text code>{{ activeSuiteId.slice(0,8) }}</el-text>
          </span>
          <div style="display:flex;gap:8px">
            <el-button type="primary" link @click="loadTraceability">Refresh Matrix</el-button>
            <el-button link @click="activeSuiteId = ''; traceabilityRows = []">Close</el-button>
          </div>
        </div>
      </template>

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
            <el-tag v-for="tcId in row.tc_ids" :key="tcId" size="small" style="margin:2px">
              {{ tcId.slice(0, 8) }}
            </el-tag>
          </template>
        </el-table-column>
      </el-table>
      <el-empty v-else description="No traceability data. Click Refresh Matrix." />
    </el-card>

    <!-- Edit dialog -->
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
          <el-button size="small" :loading="optimizing" @click="rerunOptimize">Re-analyze</el-button>
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
  listRequirements, generateTestCases, listTestSuites, deleteSuite,
  updateTestCase, deleteTestCase, getTraceability, updateStrategy,
  generateOracle, optimizeSuite
} from '../api/index.js'

const requirements = ref([])
const suites = ref([])
const selectedReqs = ref([])
const techniques = ref(['equivalence_partitioning', 'boundary_value_analysis', 'decision_table'])
const loading = ref(false)
const generating = ref(false)
const activePanels = ref([])
const activeSuiteId = ref('')

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

function formatDate(iso) {
  if (!iso) return ''
  return new Date(iso).toLocaleString()
}

async function loadRequirements() {
  const { data } = await listRequirements()
  requirements.value = data
}

async function loadSuites() {
  loading.value = true
  try {
    const { data } = await listTestSuites()
    suites.value = data
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
    ElMessage.success(`Generated ${data.tc_count} test case(s)`)
    await loadSuites()
    activePanels.value = [data.id, ...activePanels.value]
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    generating.value = false
  }
}

function selectSuite(suite) {
  activeSuiteId.value = suite.id
  strategyTechniques.value = [...(suite.techniques || [])]
  traceabilityRows.value = []
  loadTraceability()
}

async function loadTraceability() {
  if (!activeSuiteId.value) return
  try {
    const { data } = await getTraceability(activeSuiteId.value)
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
  if (!activeSuiteId.value) return
  regenerating.value = true
  try {
    const { data } = await updateStrategy(activeSuiteId.value, strategyTechniques.value)
    ElMessage.success(`Strategy updated — ${data.tc_count} test case(s) generated`)
    await loadSuites()
    await loadTraceability()
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    regenerating.value = false
  }
}

async function handleGenerateOracle(suite) {
  const ids = suite.test_cases.map(tc => tc.id)
  if (!ids.length) return ElMessage.warning('No test cases in this suite')
  activeSuiteId.value = suite.id
  generatingOracle.value = true
  try {
    const { data } = await generateOracle(ids)
    oracleResults.value = data.results
    oracleVisible.value = true
    ElMessage.success(`Oracle generated for ${data.results.length} test case(s)`)
    await loadSuites()
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    generatingOracle.value = false
  }
}

async function handleOptimize(suite) {
  activeSuiteId.value = suite.id
  optimizing.value = true
  try {
    const { data } = await optimizeSuite(suite.id, optimizeStrategy.value)
    optimizeCandidates.value = data.candidates
    selectedForRemoval.value = data.candidates.map(c => c.tc_id)
    optimizeVisible.value = true
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    optimizing.value = false
  }
}

async function rerunOptimize() {
  if (!activeSuiteId.value) return
  optimizing.value = true
  try {
    const { data } = await optimizeSuite(activeSuiteId.value, optimizeStrategy.value)
    optimizeCandidates.value = data.candidates
    selectedForRemoval.value = data.candidates.map(c => c.tc_id)
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
  await loadSuites()
}

async function handleDeleteSuite(suite) {
  try {
    await deleteSuite(suite.id)
    suites.value = suites.value.filter(s => s.id !== suite.id)
    if (activeSuiteId.value === suite.id) {
      activeSuiteId.value = ''
      traceabilityRows.value = []
    }
    ElMessage.success(`Suite and ${suite.tc_count} test case(s) deleted`)
  } catch (e) {
    ElMessage.error(e.message)
  }
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
    await loadSuites()
    ElMessage.success('Saved')
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    saving.value = false
  }
}

async function handleDeleteCase(row, suite) {
  try {
    await deleteTestCase(row.id)
    suite.test_cases = suite.test_cases.filter(tc => tc.id !== row.id)
    suite.tc_count = Math.max(0, (suite.tc_count || 0) - 1)
    ElMessage.success('Test case deleted')
  } catch (e) {
    ElMessage.error(e.message)
  }
}

onMounted(() => {
  loadRequirements()
  loadSuites()
})
</script>