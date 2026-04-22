export interface Check {
  name: string;
  status: "ok" | "warning" | "error";
  summary: string;
  suggestions: string[];
  details: Record<string, any>;
}

export interface Report {
  project_name: string;
  report_title: string;
  dataset_type: string;
  total_samples: number;
  health_score: number;
  overall_status: "healthy" | "acceptable" | "needs_attention" | "critical";
  dataset_path: string;
  generation_timestamp: string;
  splits_available: string[];
  num_classes: number;
  class_counts: Record<string, number>;
  split_counts: Record<string, number>;
  checks: Check[];
}

export const mockReport: Report = {
  project_name: "MLSanity",
  report_title: "Dataset Report",
  dataset_type: "image_classification",
  total_samples: 48_752,
  health_score: 73,
  overall_status: "needs_attention",
  dataset_path: "/data/datasets/imagenet-subset-v3",
  generation_timestamp: "2026-04-08T14:32:07Z",
  splits_available: ["train", "val", "test"],
  num_classes: 24,
  class_counts: {
    airplane: 2145, automobile: 2089, bird: 1876, cat: 2301, deer: 1654,
    dog: 2412, frog: 1987, horse: 2076, ship: 2198, truck: 1932,
    bicycle: 1567, bus: 1423, car: 2654, motorbike: 1298, person: 3201,
    bottle: 987, chair: 1456, table: 1123, plant: 876, sofa: 1045,
    monitor: 1234, train_vehicle: 1567, cow: 987, sheep: 738
  },
  split_counts: {
    train: 34_126,
    val: 7_313,
    test: 7_313
  },
  checks: [
    {
      name: "corruption",
      status: "ok",
      summary: "No corrupted samples detected in the dataset.",
      suggestions: [],
      details: {
        total_checked: 48752,
        corrupted_count: 0,
        corruption_rate: 0.0
      }
    },
    {
      name: "duplicates",
      status: "warning",
      summary: "Found 127 exact duplicate pairs across the dataset.",
      suggestions: [
        "Remove exact duplicates to prevent data leakage",
        "Check if duplicates span across train/val/test splits"
      ],
      details: {
        duplicate_count: 127,
        duplicate_rate: 0.0026,
        groups: [
          { group_id: 1, sample_ids: ["img_0042", "img_12876"], hash: "a3f8c2...d91e" },
          { group_id: 2, sample_ids: ["img_0198", "img_33421"], hash: "b7e1a0...f423" },
          { group_id: 3, sample_ids: ["img_1042", "img_8761", "img_22103"], hash: "c9d2f1...8a7b" },
          { group_id: 4, sample_ids: ["img_2301", "img_45012"], hash: "d1e3f4...2c9d" },
          { group_id: 5, sample_ids: ["img_3876", "img_9432"], hash: "e2f4a5...3d0e" }
        ]
      }
    },
    {
      name: "near_duplicates",
      status: "warning",
      summary: "Detected 43 near-duplicate pairs with cosine similarity > 0.95.",
      suggestions: [
        "Review near-duplicate pairs manually",
        "Consider increasing similarity threshold if pairs are acceptable"
      ],
      details: {
        threshold: 0.95,
        pair_count: 43,
        pair_examples: [
          { id_a: "img_0421", id_b: "img_12003", similarity: 0.982 },
          { id_a: "img_1987", id_b: "img_34210", similarity: 0.971 },
          { id_a: "img_4523", id_b: "img_8901", similarity: 0.965 },
          { id_a: "img_6712", id_b: "img_19834", similarity: 0.958 },
          { id_a: "img_7890", id_b: "img_23456", similarity: 0.953 }
        ]
      }
    },
    {
      name: "leakage",
      status: "error",
      summary: "Data leakage detected: 89 samples appear in both train and test splits.",
      suggestions: [
        "Immediately remove leaked samples from the test set",
        "Re-split the dataset using a deterministic hash-based approach",
        "Audit the data pipeline for split contamination"
      ],
      details: {
        leaked_count: 89,
        leaked_pairs: [
          { train_id: "img_0012", test_id: "img_41023" },
          { train_id: "img_0098", test_id: "img_42156" },
          { train_id: "img_0234", test_id: "img_43789" },
          { train_id: "img_0567", test_id: "img_44012" }
        ],
        affected_classes: ["cat", "dog", "person", "car"]
      }
    },
    {
      name: "leakage_near",
      status: "warning",
      summary: "23 near-duplicate pairs found spanning train/test boundary.",
      suggestions: [
        "Review near-leakage pairs and remove from test if confirmed",
        "Use perceptual hashing for more robust split validation"
      ],
      details: {
        threshold: 0.92,
        pair_count: 23,
        pair_examples: [
          { train_id: "img_1234", test_id: "img_40567", distance: 0.078 },
          { train_id: "img_2345", test_id: "img_41678", distance: 0.065 },
          { train_id: "img_3456", test_id: "img_42789", distance: 0.082 }
        ]
      }
    },
    {
      name: "imbalance",
      status: "warning",
      summary: "Class imbalance detected. Ratio of largest to smallest class is 4.34:1.",
      suggestions: [
        "Apply oversampling (SMOTE) or undersampling for minority classes",
        "Use class weights during training",
        "Consider data augmentation for underrepresented classes"
      ],
      details: {
        imbalance_ratio: 4.34,
        largest_class: { name: "person", count: 3201 },
        smallest_class: { name: "sheep", count: 738 },
        gini_coefficient: 0.18,
        entropy: 3.12
      }
    },
    {
      name: "schema",
      status: "ok",
      summary: "Dataset schema is consistent across all samples.",
      suggestions: [],
      details: {
        fields_checked: ["image", "label", "split", "metadata"],
        missing_fields: 0,
        type_mismatches: 0,
        schema: {
          image: "bytes",
          label: "string",
          split: "string",
          metadata: "dict"
        }
      }
    },
    {
      name: "label_hints",
      status: "error",
      summary: "Detected 34 potentially mislabeled samples based on model confidence.",
      suggestions: [
        "Manually review flagged samples",
        "Consider re-labeling or removing ambiguous samples",
        "Run a second model for cross-validation"
      ],
      details: {
        total_suspicious: 34,
        confidence_threshold: 0.85,
        candidates: [
          { sample_id: "img_4521", current_label: "cat", suspected_label: "dog", score: 0.94, reason: "High confidence mismatch" },
          { sample_id: "img_8903", current_label: "automobile", suspected_label: "truck", score: 0.91, reason: "Ambiguous boundary" },
          { sample_id: "img_12045", current_label: "bird", suspected_label: "airplane", score: 0.89, reason: "Shape similarity" },
          { sample_id: "img_15678", current_label: "deer", suspected_label: "horse", score: 0.88, reason: "Pose ambiguity" },
          { sample_id: "img_19234", current_label: "frog", suspected_label: "plant", score: 0.87, reason: "Color/texture overlap" },
          { sample_id: "img_22567", current_label: "ship", suspected_label: "bus", score: 0.86, reason: "Low resolution" }
        ]
      }
    }
  ]
};
