def solver_bfs(self) -> list[tuple[int, int]]:
    """Find corridor from ENTRY to EXIT as BFS.
    """
    # kolejka do sprawdzania komorek (linked lista dwustronna)
    queue: deque[tuple[int, int]] = deque([self.entry])

    # odwiedzone, zeby nie sprawdzac dwa razy
    visited: set[tuple[int, int]] = {self.entry}

    # slownik a'la linked lista, key to gdzie jestem, value to skad
    # przyszedlem

    came_from: dict[tuple[int, int], tuple[int, int] | None] \
        = {self.entry: None}

    # mapa ruchow jak w DIRECTIONS, ale tutaj tupla jako wektor w key,
    # jedna sciana jako value
    moves = {
        (0, -1): Wall.N,  # Ruch w górę
        (1, 0): Wall.E,  # Ruch w prawo
        (0, 1): Wall.S,  # Ruch w dół
        (-1, 0): Wall.W  # Ruch w lewo
    }

    # glowna petla, FIFO, popleft wyciaga x, y z pierwszego elementu
    # i go usuwa z kolejki, krecimy sie w petli dopoki nie staniemy na EXIT
    while queue:
        current: tuple[int, int] | None = queue.popleft()

        if current == self.exit:
            break

        if current is not None:
            x, y = current

        # sprawdzamy sciany
        for (dx, dy), wall_flag in moves.items():
            nx, ny = x + dx, y + dy

            # zabezpieczenie na zewnetrzne sciany i na znak 42, chociaz
            # one tam sa wiec nie powinnismy wyjsc poza plansze
            if (0 <= nx < self.width and 0 <= ny < self.height
                    and (nx, ny) not in self.locked_cells):

                # bitowe porownanie sciany z moves, ze sciana w self.grid
                if (self.grid[y][x] & wall_flag) == 0:

                    if (nx, ny) not in visited:
                        visited.add((nx, ny))
                        came_from[(nx, ny)] = current
                        queue.append((nx, ny))

    # sciezka
    path = []
    curr: tuple[int, int] | None = self.exit

    if curr not in came_from:
        print("?")
        return []

    while curr is not None:
        path.append(curr)
        curr = came_from[curr]

    # odwraca liste path, teraz entry jest jako pierwsze
    path.reverse()
    self.path = path
    return path
