#!/usr/bin/env python3
"""Patch setCacheOccupancy to add bounds checking."""
import sys

path = '/root/ego_ws/src/ego-planner-swarm/src/planner/plan_env/src/grid_map.cpp'
with open(path, 'r') as f:
    content = f.read()

old = """int GridMap::setCacheOccupancy(Eigen::Vector3d pos, int occ)
{
  if (occ != 1 && occ != 0)
    return INVALID_IDX;

  Eigen::Vector3i id;
  posToIndex(pos, id);
  int idx_ctns = toAddress(id);"""

new = """int GridMap::setCacheOccupancy(Eigen::Vector3d pos, int occ)
{
  if (occ != 1 && occ != 0)
    return INVALID_IDX;

  Eigen::Vector3i id;
  posToIndex(pos, id);

  // Bounds check to prevent SIGSEGV when points are outside map
  for (int i = 0; i < 3; ++i)
  {
    if (id(i) < 0 || id(i) >= mp_.map_voxel_num_(i))
      return INVALID_IDX;
  }

  int idx_ctns = toAddress(id);"""

if old in content:
    content = content.replace(old, new)
    with open(path, 'w') as f:
        f.write(content)
    print('PATCHED OK')
else:
    print('OLD STRING NOT FOUND')
    sys.exit(1)
