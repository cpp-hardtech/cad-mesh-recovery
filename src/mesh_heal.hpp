// cad_mesh_recovery — mesh-level stitch of open boundaries (D-fc-5.10).
//
// Defined in cad_mesh_recovery.cpp next to absorbZeroAreaTJunctions; declared here so
// tests/unit/heal_open_boundaries_unit.cpp can drive it on synthetic meshes.
//
// SPDX-License-Identifier: MIT

#ifndef CAD_MESH_RECOVERY_MESH_HEAL_HPP
#define CAD_MESH_RECOVERY_MESH_HEAL_HPP

#include <array>
#include <vector>

namespace cad_mesh_recovery {
namespace detail {

struct HealStats {
    int boundaryBefore = 0;      // edges used once on input
    int boundaryAfter = 0;       // edges used once on output
    int welds = 0;               // vertices welded (healed clusters only)
    int collapsed = 0;           // triangles dropped by a weld (healed clusters only)
    int splits = 0;              // vertex-on-edge splits (healed clusters only)
    int refusedWeldClusters = 0; // weld clusters wider than stitchTol
    int clustersHealed = 0;      // stitched clusters that passed the certificate
    int clustersRefused = 0;     // clusters with an open edge that keep their input
    double sMin = 0;             // shortest edge longer than tau
    double stitchTol = 0;        // min(sewTol, sMin / 2)
    double weldMax = 0;          // longest weld (healed clusters only)
    double splitMax = 0;         // farthest split vertex from its edge (healed clusters only)
};

// tris is rewritten only when at least one cluster heals. tau = 2·quantFloor.
// quantFloor <= 0, a mesh with no open edge, or any non-finite vertex
// coordinate or edge length (D-fc-5.19) returns with tris untouched.
HealStats healOpenBoundaries(std::vector<std::array<int, 3>>& tris,
                             const std::vector<std::array<double, 3>>& pts,
                             double quantFloor, double sewTol, bool diag);

}  // namespace detail
}  // namespace cad_mesh_recovery

#endif
